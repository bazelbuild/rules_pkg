_default_attrs = "user=root;group=root"
_manifest = [
    #action     dest                                            attributes...                       source
    ("copy",    "/etc/syslog.conf.d/mycomponent.conf",          "unix=0644;section=confignoreplace", "//mycomponent/etc:conf"),
    ("copy",    "/opt/mycomponent/lib/",                        "unix=0755",                         ":libs_collected"),
    ("copy",    "/opt/mycomponent/etc/",                        "unix=0600;section=confignoreplace", ":secret_properties"),
    ("copy",    "/opt/mycomponent/etc/",                        "unix=0644;section=confignoreplace", "//mycomponent/etc:foo.properties"),
    ("copy",    "/opt/mycomponent/etc/",                        "unix=0644;section=confignoreplace", "//mycomponent/etc:bar.properties"),
    ("copy",    "/opt/mycomponent/etc/",                        "unix=0644;section=confignoreplace", "//mycomponent/etc:foobar.properties"),
    ("copy",    "/opt/mycomponent/etc/",                        "unix=0644;section=confignoreplace", "//mycomponent/etc:idkmybffjill.properties"),
    ("copy",    "/opt/mycomponent/etc/",                        "unix=0644;section=confignoreplace", "//mycomponent/etc/some/subpackage:subpackage.properties"),
    ("copy",    "/opt/mycomponent/resources/i18n/en_us",        "unix=0644",                         "@i18n//mycomponent/en_us"),
    ("copy",    "/opt/mycomponent/resources/i18n/en_gb",        "unix=0644",                         "@i18n//mycomponent/en_gb"),
    ("copy",    "/opt/mycomponent/resources/i18n/es_es",        "unix=0644",                         "@i18n//mycomponent/es_es"),
    ("copy",    "/opt/mycomponent/resources/i18n/es_mx",        "unix=0644",                         "@i18n//mycomponent/es_mx"),
    ("copy",    "/opt/mycomponent/bin/mycomponent-service.bin", "unix=0755",                         "//mycomponent/src:service.bin"),
    ("copy",    "/opt/mycomponent/bin/mycomponent-runner",      "unix=0755",                         "//mycomponent/src:runner"),
    ("symlink", "/usr/bin/mycomponentd",                        "",                                  "/opt/mycomponent/bin/mycomponent-service-runner"),

    ("mkdir",   "/opt/mycomponent",                             "unix=0755",                         ""),
    ("mkdir",   "/opt/mycomponent/lib",                         "unix=0755",                         ""),
    ("mkdir",   "/opt/mycomponent/resources",                   "unix=0755",                         ""),
    ("mkdir",   "/opt/mycomponent/state",                       "unix=0755",                         ""),
    ("mkdir",   "/opt/mycomponent/resources/i18n",              "unix=0755",                         ""),
]


manifest_info = {
    "default_attrs": _default_attrs,
    "manifest": _manifest,
}
