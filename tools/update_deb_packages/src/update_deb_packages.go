package main

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"reflect"
	"sort"
	"strings"

	"golang.org/x/crypto/openpgp"

	"github.com/knqyf263/go-deb-version"
	"github.com/stapelberg/godebiancontrol"
)

var FORCE_PACKAGE_IDENT = `{
  "IsListArg": {
    "packages": false
  }
}
`

func appendUniq(slice []string, v string) []string {
	for _, x := range slice {
		if x == v {
			return slice
		}
	}
	return append(slice, v)
}

func logFatalErr(e error) {
	if e != nil {
		log.Fatal(e)
	}
}

// https://stackoverflow.com/a/33853856/5441396
func downloadFile(filepath string, url string) (err error) {

	// Create the file
	out, err := os.Create(filepath)
	if err != nil {
		return err
	}
	defer out.Close()

	// Get the data
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	if resp.StatusCode != 200 {
		return fmt.Errorf("Download from %s failed with statuscode %d", url, resp.StatusCode)
	}
	defer resp.Body.Close()

	// Writer the body to file
	_, err = io.Copy(out, resp.Body)
	if err != nil {
		return err
	}

	return nil
}

func getFileFromURLList(filepath string, filename string, urls []string) {
	// no chunked downloads, just tries URLs one by one until it succeeds or fails because no URLs are left
	success := false

	for _, u := range urls {
		parsed, err := url.Parse(u)
		logFatalErr(err)
		err = downloadFile(filepath, parsed.String())
		if err != nil {
			log.Print(err)
		} else {
			success = true
			// log.Printf("Sucessfully fetched %s\n", parsed.String())
			break
		}
	}
	if success == false {
		log.Fatalf("No mirror had the file %s available.\n URLS: %s", filename, urls)
	}
}

func getFileFromMirror(filepath string, filename string, distro string, mirrors []string) {
	urls := make([]string, 0)
	for _, mirror := range mirrors {
		baseURL, err := url.Parse(mirror)
		logFatalErr(err)
		ref, err := url.Parse(path.Join(baseURL.Path, "dists", distro, filename))
		logFatalErr(err)
		urls = append(urls, baseURL.ResolveReference(ref).String())
	}
	getFileFromURLList(filepath, filename, urls)
}

func compareFileWithHash(filepath string, sha256Hash string) bool {
	target, err := hex.DecodeString(sha256Hash)
	logFatalErr(err)

	f, err := os.Open(filepath)
	logFatalErr(err)
	defer f.Close()

	h := sha256.New()
	_, err = io.Copy(h, f)
	logFatalErr(err)

	actual := h.Sum(nil)

	if bytes.Equal(actual, target) != true {
		log.Printf("Hash mismatch: Expected %x, got %x", target, actual)
	}

	return bytes.Equal(actual, target)
}

func checkPgpSignature(keyfile string, checkfile string, sigfile string) {
	key, err := os.Open(keyfile)
	logFatalErr(err)

	sig, err := os.Open(sigfile)
	logFatalErr(err)

	check, err := os.Open(checkfile)
	logFatalErr(err)

	keyring, err := openpgp.ReadArmoredKeyRing(key)
	logFatalErr(err)

	_, err = openpgp.CheckArmoredDetachedSignature(keyring, check, sig)
	logFatalErr(err)
}

func getPackages(arch string, distroType string, distro string, mirrors []string, components []string, pgpKeyFile string) (packages []godebiancontrol.Paragraph) {
	releasefile, err := ioutil.TempFile("", "Release")
	logFatalErr(err)

	releasegpgfile, err := ioutil.TempFile("", "Releasegpg")
	logFatalErr(err)

	// download Release + Release.gpg
	getFileFromMirror(releasefile.Name(), "Release", distro, mirrors)
	getFileFromMirror(releasegpgfile.Name(), "Release.gpg", distro, mirrors)

	// check signature
	checkPgpSignature(pgpKeyFile, releasefile.Name(), releasegpgfile.Name())

	os.Remove(releasegpgfile.Name())

	// read/parse Release file
	release, err := godebiancontrol.Parse(releasefile)
	logFatalErr(err)
	os.Remove(releasefile.Name())

	// this will be the merged Packages file
	packagesfile, err := ioutil.TempFile("", "Packages")
	logFatalErr(err)

	// download all binary-<arch> Packages.gz files
	for _, line := range strings.Split(release[0]["SHA256"], "\n") {
		fields := strings.Fields(line)
		if len(fields) == 0 {
			//last line is an empty line
			continue
		}
		hash := fields[0]
		path := fields[2]
		isAcceptedComponent := true
		if len(components) > 0 {
			isAcceptedComponent = false
			for _, component := range components {
				if strings.HasPrefix(path, component+"/") {
					isAcceptedComponent = true
					break
				}
			}
		}
		if isAcceptedComponent && strings.HasSuffix(path, "/binary-"+arch+"/Packages.gz") {
			tmpPackagesfile, err := ioutil.TempFile("", "Packages")
			logFatalErr(err)
			getFileFromMirror(tmpPackagesfile.Name(), path, distro, mirrors)
			// check hash of Packages.gz files
			if compareFileWithHash(tmpPackagesfile.Name(), hash) != true {
				log.Fatalf("Downloaded file %s corrupt", path)
			}

			// unzip Packages.gz files
			handle, err := os.Open(tmpPackagesfile.Name())
			logFatalErr(err)
			defer handle.Close()

			zipReader, err := gzip.NewReader(handle)
			logFatalErr(err)
			defer zipReader.Close()

			content, err := ioutil.ReadAll(zipReader)
			logFatalErr(err)
			os.Remove(tmpPackagesfile.Name())

			// append content to merged Packages file
			f, err := os.OpenFile(packagesfile.Name(), os.O_APPEND|os.O_WRONLY, 0600)
			logFatalErr(err)
			defer f.Close()

			_, err = f.Write(content)
			logFatalErr(err)
		}
	}

	// read/parse merged Packages file
	parsed, err := godebiancontrol.Parse(packagesfile)
	logFatalErr(err)
	os.Remove(packagesfile.Name())

	return parsed
}

func getStringField(fieldName string, fileName string, ruleName string, workspaceContents []byte) string {
	// buildozer 'print FIELDNAME_GOES_HERE' FILENAME_GOES_HERE:RULENAME_GOES_HERE <WORKSPACE
	cmd := exec.Command("buildozer", "print "+fieldName, fileName+":"+ruleName)
	wsreader := bytes.NewReader(workspaceContents)
	if fileName == "-" {
		// see edit.stdinPackageName why this is a "-"
		cmd.Stdin = wsreader
	}
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		exiterr, ok := err.(*exec.ExitError)
		if ok == true {
			// not every platform might have exit codes
			// see https://groups.google.com/forum/#!topic/golang-nuts/MI4TyIkQqqg
			exitCode := exiterr.Sys().(interface {
				ExitStatus() int
			}).ExitStatus()
			// Return code 3 is the intended behaviour for buildozer when using "print" commands
			if exitCode != 3 {
				log.Print("Error in getStringField, command: ", cmd)
				logFatalErr(err)
			}
		} else {
			logFatalErr(err)
		}
	}

	// remove trailing newline
	return strings.TrimSpace(out.String())
}

func getListField(fieldName string, fileName string, ruleName string, workspaceContents []byte) []string {
	// buildozer 'print FIELDNAME_GOES_HERE' FILENAME_GOES_HERE:RULENAME_GOES_HERE <WORKSPACE
	// TODO: better failure message if buildozer is not in PATH
	cmd := exec.Command("buildozer", "print "+fieldName, fileName+":"+ruleName)
	wsreader := bytes.NewReader(workspaceContents)
	if fileName == "-" {
		// see edit.stdinPackageName why this is a "-"
		cmd.Stdin = wsreader
	}
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		exiterr, ok := err.(*exec.ExitError)
		if ok == true {
			// not every platform might have exit codes
			// see https://groups.google.com/forum/#!topic/golang-nuts/MI4TyIkQqqg
			exitCode := exiterr.Sys().(interface {
				ExitStatus() int
			}).ExitStatus()
			// Return code 3 is the intended behaviour for buildozer when using "print" commands
			if exitCode != 3 {
				log.Print("Error in getListField, command: ", cmd)
				logFatalErr(err)
			}
		} else {
			logFatalErr(err)
		}
	}

	trimmedOut := strings.TrimSpace(out.String())
	if trimmedOut == "(missing)" {
		return []string{}
	}
	var resultlist []string
	// remove trailing newline, remove [] and split at spaces
	returnlist := strings.Split(strings.Replace(strings.Trim(trimmedOut, "[]"), "\n", ",", -1), " ")
	// also split at commas
	for _, result := range returnlist {
		resultlist = append(resultlist, strings.Split(result, ",")...)
	}

	// Example output for querying a missing field:
	// rule "//-:foo" has no attribute "bar"
	// (missing)
	if len(resultlist) == 2 {
		if resultlist[1] == "(missing)" {
			return []string{}
		}
	}

	return resultlist
}

func getMapField(fieldName string, fileName string, ruleName string, workspaceContents []byte) map[string]string {
	// buildozer 'print FIELDNAME_GOES_HERE' FILENAME_GOES_HERE:RULENAME_GOES_HERE <WORKSPACE
	cmd := exec.Command("buildozer", "print "+fieldName, fileName+":"+ruleName)
	wsreader := bytes.NewReader(workspaceContents)
	if fileName == "-" {
		// see edit.stdinPackageName why this is a "-"
		cmd.Stdin = wsreader
	}
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		exiterr, ok := err.(*exec.ExitError)
		if ok == true {
			// not every platform might have exit codes
			// see https://groups.google.com/forum/#!topic/golang-nuts/MI4TyIkQqqg
			exitCode := exiterr.Sys().(interface {
				ExitStatus() int
			}).ExitStatus()
			// Return code 3 is the intended behaviour for buildozer when using "print" commands
			if exitCode != 3 {
				log.Print("Error in getMapField, command: ", cmd)
				logFatalErr(err)
			}
		} else {
			logFatalErr(err)
		}
	}
	m := make(map[string]string)

	for _, line := range strings.Split(out.String(), "\n") {
		var key string
		for i, token := range strings.Split(strings.Trim(strings.TrimSpace(line), ",{}"), ":") {
			if i%2 == 0 {
				// new key
				key = strings.Trim(token, " \"")
			} else {
				// value (new key was set in previous iteration)
				m[key] = strings.Trim(token, " \"")
			}
		}
	}
	return m
}

func getAllLabels(labelName string, fileName string, ruleName string, workspaceContents []byte) map[string][]string {
	// buildozer 'print label LABELNAME_GOES_HERE' FILENAME_GOES_HERE:RULENAME_GOES_HERE <WORKSPACE
	cmd := exec.Command("buildozer", "print label "+labelName, fileName+":"+ruleName)
	wsreader := bytes.NewReader(workspaceContents)
	if fileName == "-" {
		// see edit.stdinPackageName why this is a "-"
		cmd.Stdin = wsreader
	}
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		exiterr, ok := err.(*exec.ExitError)
		if ok == true {
			// not every platform might have exit codes
			// see https://groups.google.com/forum/#!topic/golang-nuts/MI4TyIkQqqg
			exitCode := exiterr.Sys().(interface {
				ExitStatus() int
			}).ExitStatus()
			// Return code 3 is the intended behaviour for buildozer when using "print" commands
			if exitCode != 3 {
				log.Print("Error in getAllLabels, command: ", cmd)
				logFatalErr(err)
			}
		} else {
			logFatalErr(err)
		}
	}

	// output is quite messed up... best indication for useful lines is that a line ending in "," contains stuff we look for.
	pkgs := make(map[string][]string)

	for _, line := range strings.Split(out.String(), "\n") {
		if strings.HasSuffix(line, ",") {
			name := strings.TrimSpace(strings.Split(line, "[")[0])
			pkgs[name] = appendUniq(pkgs[name], strings.Trim(strings.TrimSpace(strings.Split(line, "[")[1]), "\",]"))
		}
	}
	return pkgs
}

func setStringField(fieldName string, fieldContents string, fileName string, ruleName string, workspaceContents []byte, forceTable *string) string {
	// buildozer 'set FIELDNAME_GOES_HERE FIELDCONTENTS_GO_HERE' FILENAME_GOES_HERE:RULENAME_GOES_HERE <WORKSPACE
	// log.Printf("(setStringField) buildozer 'set %s %s' %s:%s\n", fieldName, fieldContents, fileName, ruleName)
	var cmd *exec.Cmd
	if forceTable != nil {
		dir, err := ioutil.TempDir("", "table_hack")
		defer os.RemoveAll(dir)
		if err != nil {
			logFatalErr(err)
		}
		tableFile := filepath.Join(dir, "force_table.json")
		if err := ioutil.WriteFile(tableFile, []byte(*forceTable), 0666); err != nil {
			logFatalErr(err)
		}
		cmd = exec.Command("buildozer", "-add_tables="+tableFile, "set "+fieldName+" "+fieldContents, fileName+":"+ruleName)
	} else {
		cmd = exec.Command("buildozer", "set "+fieldName+" "+fieldContents, fileName+":"+ruleName)
	}
	wsreader := bytes.NewReader(workspaceContents)
	if fileName == "-" {
		// see edit.stdinPackageName why this is a "-"
		cmd.Stdin = wsreader
	}
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		exiterr, ok := err.(*exec.ExitError)
		if ok == true {
			// not every platform might have exit codes
			// see https://groups.google.com/forum/#!topic/golang-nuts/MI4TyIkQqqg
			exitCode := exiterr.Sys().(interface {
				ExitStatus() int
			}).ExitStatus()
			// Return code 3 is the intended behaviour for buildozer when using "set" commands that don't change anything
			if exitCode != 3 {
				log.Print("Error in setStringField, command: ", cmd)
				logFatalErr(err)
			}
		} else {
			logFatalErr(err)
		}
	}

	return out.String()
}

func updateWorkspaceRule(workspaceContents []byte, rule string) string {
	arch := getStringField("arch", "-", rule, workspaceContents)
	distroType := getStringField("distro_type", "-", rule, workspaceContents)
	distro := getStringField("distro", "-", rule, workspaceContents)
	mirrors := getListField("mirrors", "-", rule, workspaceContents)
	components := getListField("components", "-", rule, workspaceContents)
	packages := getMapField("packages", "-", rule, workspaceContents)
	packagesSha256 := getMapField("packages_sha256", "-", rule, workspaceContents)
	pgpKeyRuleName := getStringField("pgp_key", "-", rule, workspaceContents)

	packageNames := make([]string, 0, len(packages))
	for p := range packages {
		packageNames = append(packageNames, p)
	}
	sort.Strings(packageNames)

	packageShaNames := make([]string, 0, len(packagesSha256))
	for p := range packages {
		packageShaNames = append(packageShaNames, p)
	}
	sort.Strings(packageShaNames)
	if reflect.DeepEqual(packageNames, packageShaNames) == false {
		log.Fatalf("Mismatch between package names in packages and packages_sha256 in rule %s.\npackages: %s\npackages_sha256: %s", rule, packageNames, packageShaNames)
	}

	wd, err := os.Getwd()
	projectName := path.Base(wd)
	pgpKeyname := path.Join("bazel-"+projectName, "external", pgpKeyRuleName, "file", "downloaded")

	allPackages := getPackages(arch, distroType, distro, mirrors, components, pgpKeyname)

	newPackages := make(map[string]string)
	newPackagesSha256 := make(map[string]string)

	for _, pack := range packageNames {
		packlist := strings.Split(pack, "=")
		var packname string
		var packversion string
		var targetVersion version.Version
		if len(packlist) > 1 && packlist[1] != "latest" {
			packname = packlist[0]
			packversion = packlist[1]
			var err error
			targetVersion, err = version.NewVersion(packlist[1])
			logFatalErr(err)
		} else {
			packname = packlist[0]
			packversion = "latest"
			var err error
			targetVersion, err = version.NewVersion("0")
			logFatalErr(err)
		}

		done := false
		for _, pkg := range allPackages {
			if pkg["Package"] == packname {
				currentVersion, err := version.NewVersion(pkg["Version"])
				logFatalErr(err)
				if packversion == "latest" {
					// iterate over all packages and keep the highest version
					if targetVersion.LessThan(currentVersion) {
						newPackages[pack] = pkg["Filename"]
						newPackagesSha256[pack] = pkg["SHA256"]
						targetVersion = currentVersion
						done = true
					}
				} else {
					// version is fixed, break once found
					if targetVersion.Equal(currentVersion) {
						newPackages[pack] = pkg["Filename"]
						newPackagesSha256[pack] = pkg["SHA256"]
						done = true
						break
					}
				}
			}
		}
		if done == false {
			log.Fatalf("Package %s isn't available in %s (rule: %s)", pack, distro, rule)
		}
	}

	pkgstring, err := json.Marshal(newPackages)
	logFatalErr(err)
	pkgshastring, err := json.Marshal(newPackagesSha256)
	logFatalErr(err)

	// set packages
	workspaceContents = []byte(setStringField("packages", string(pkgstring), "-", rule, workspaceContents, &FORCE_PACKAGE_IDENT))
	// set packages_sha256
	workspaceContents = []byte(setStringField("packages_sha256", string(pkgshastring), "-", rule, workspaceContents, nil))
	// final run that just replaces a known value with itself to make sure the output is prettyfied
	workspaceContents = []byte(setStringField("distro", "\""+distro+"\"", "-", rule, workspaceContents, nil))

	return string(workspaceContents)
}

func updateWorkspace(workspaceContents []byte) string {
	rules := getListField("name", "-", "%deb_packages", workspaceContents)
	cleanedRules := make([]string, len(rules))
	copy(cleanedRules, rules)

	for i, rule := range rules {
		tags := getListField("tags", "-", rule, workspaceContents)
		for _, tag := range tags {
			// drop rules with the "manual_update" tag
			if tag == "manual_update" {
				cleanedRules = append(cleanedRules[:i], cleanedRules[i+1:]...)
			}
		}
	}

	for _, rule := range cleanedRules {
		workspaceContents = []byte(updateWorkspaceRule(workspaceContents, rule))
	}
	return string(workspaceContents)
}

// add new package names to WORKSPACE rule
func addNewPackagesToWorkspace(workspaceContents []byte) string {
	// TODO: add more rule types here if necessary
	// e.g. cacerts()
	allDebs := make(map[string][]string)
	for _, rule_type := range []string{"container_layer", "container_image"} {
		tmp := getAllLabels("debs", "//...", "%"+rule_type, workspaceContents)
		for k, _ := range tmp {
			if _, ok := allDebs[k]; !ok {
				allDebs[k] = make([]string, 0)
			}
			for _, pack := range tmp[k] {
				allDebs[k] = appendUniq(allDebs[k], pack)
			}
		}
	}

	for rule := range allDebs {
		tags := getListField("tags", "-", rule, workspaceContents)
		for _, tag := range tags {
			// drop rules with the "manual_update" tag
			if tag == "manual_update" {
				delete(allDebs, rule)
			}
		}
	}

	for rule, debs := range allDebs {
		packages := getMapField("packages", "-", rule, workspaceContents)
		packagesSha256 := getMapField("packages_sha256", "-", rule, workspaceContents)
		for _, deb := range debs {
			packages[deb] = "placeholder"
			packagesSha256[deb] = "placeholder"
		}

		pkgstring, err := json.Marshal(packages)
		logFatalErr(err)
		pkgshastring, err := json.Marshal(packagesSha256)
		logFatalErr(err)

		// set packages
		workspaceContents = []byte(setStringField("packages", string(pkgstring), "-", rule, workspaceContents, &FORCE_PACKAGE_IDENT))
		// set packages_sha256
		workspaceContents = []byte(setStringField("packages_sha256", string(pkgshastring), "-", rule, workspaceContents, nil))
	}

	return string(workspaceContents)
}

// update WORKSPACE rule with new paths/hashes from mirrors
func main() {
	workspacefile, err := os.Open("WORKSPACE")
	logFatalErr(err)
	wscontent, err := ioutil.ReadAll(workspacefile)
	logFatalErr(err)
	workspacefile.Close()

	err = ioutil.WriteFile("WORKSPACE", []byte(updateWorkspace([]byte(addNewPackagesToWorkspace(wscontent)))), 0664)
	logFatalErr(err)

}
