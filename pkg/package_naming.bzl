

def default_package_naming(ctx):
  if in ctx.attr["stamp"]:
    stamp = str(ctx.attrs.stamp)
  else:
    stamp = "NO_STAMP"
  values = {}
  values['stamp'] = stamp
  values['BUILD_HOST'] = 'host'
  values['BUILD_USER'] = 'user'
  # Jan 1, 1980
  values['BUILD_TIMESTAMP'] = 315532800
  return values
