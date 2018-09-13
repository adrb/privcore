How to build a minified version of converse.js for this plugin
==============================================================

The default convers.min.js script includes jquery which is already integrated 
part of Roundcube. Thus including it will cause conflicts and massive errors.

The following instructions describe how to build the converse.js minified
script for the use in Roundcube.

1. Exclude the jquery dependency from the converse.js build files using the 
diff from this package:
  ```
  cd devel/converse.js
  patch -p1 < ../../build/converse_build.diff
  ```
2. Run the build process
  ```
  cd devel/converse.js
  make dev
  make build
  ```

3. Copy the necessary resources from converse.js
   ```
   cp devel/converse.js/builds/converse.min.js js/
   cp devel/converse.js/builds/converse-no-locales-no-otr.min.js js/
   cp devel/converse.js/builds/converse-no-otr.min.js js/
   cp devel/converse.js/builds/templates.js js/
   cp -r devel/converse.js/css/* css/
   cp -r devel/converse.js/fonticons .
   ```

[conversedocs]: http://conversejs.org/docs/html/index.html#development
