_default_attrs = "user=root;group=root"
_manifest = [
    #dest                                            action     attributes...                          source
    ("/etc/syslog.conf.d/mycomponent.conf",          "copy",    "unix=0644;section=config(noreplace)", "//mycomponent/etc:conf"),
    ("/opt/mycomponent/lib/",                        "copy",    "unix=0755",                           ":libs_collected"),
    ("/opt/mycomponent/etc/",                        "copy",    "unix=0600;section=config(noreplace)", ":secret_properties"),
    ("/opt/mycomponent/etc/",                        "copy",    "unix=0644;section=config(noreplace)", "//mycomponent/etc:foo.properties"),
    ("/opt/mycomponent/etc/",                        "copy",    "unix=0644;section=config(noreplace)", "//mycomponent/etc:bar.properties"),
    ("/opt/mycomponent/etc/",                        "copy",    "unix=0644;section=config(noreplace)", "//mycomponent/etc:foobar.properties"),
    ("/opt/mycomponent/etc/",                        "copy",    "unix=0644;section=config(noreplace)", "//mycomponent/etc:idkmybffjill.properties"),
    ("/opt/mycomponent/etc/",                        "copy",    "unix=0644;section=config(noreplace),", "//mycomponent/etc/some/subpackage:subpackage.properties")2,
    ("/opt/mycomponent/resources/i18n/en_us",        "copy",    "unix=0644",                           "@i18n//mycomponent/en_us"),
    ("/opt/mycomponent/resources/i18n/en_gb",        "copy",    "unix=0644",                           "@i18n//mycomponent/en_gb"),
    ("/opt/mycomponent/resources/i18n/es_es",        "copy",    "unix=0644",                           "@i18n//mycomponent/es_es"),
    ("/opt/mycomponent/resources/i18n/es_mx",        "copy",    "unix=0644",                           "@i18n//mycomponent/es_mx"),
    ("/opt/mycomponent/bin/mycomponent-service.bin", "copy",    "unix=0755",                           "//mycomponent/src:service.bin"),
    ("/opt/mycomponent/bin/mycomponent-runner",      "copy",    "unix=0755",                           "//mycomponent/src:runner"),
    ("/usr/bin/mycomponentd",                        "symlink", "",                                    "/opt/mycomponent/bin/mycomponent-service-runner"),

    ("/opt/mycomponent",                             "mkdir",   "unix=0755",                           ""),
    ("/opt/mycomponent/lib",                         "mkdir",   "unix=0755",                           ""),
    ("/opt/mycomponent/resources",                   "mkdir",   "unix=0755",                           ""),
    ("/opt/mycomponent/state",                       "mkdir",   "unix=0755",                           ""),
    ("/opt/mycomponent/resources/i18n",              "mkdir",   "unix=0755",                           ""),

]

manifest_info = {
    "default_attrs": _default_attrs,
    "manifest": _manifest,
}
