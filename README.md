# air
Air is a wrapper around developing for Minecraft: Bedrock Edition. At it's core, it keeps two directories in sync: a development directory and the resource and behavior pack folders of the world being worked on.

Air's true power, however, comes from its processing capabilites during this syncing. For example, the `mcjson` converter transparently and, more importantly, bidirectionally converts between  `.mcj` files in the development folder and `.json` files in the world.

Air also supports plugins which can do simple one-time tasks such as setting up base entities to work off of, generating syntax summaries, or any multitude of things.

## Syncing
On startup, Air syncs the two directories.
It first iterates through the development directory and runs the converters on each file, and compares the output with the existing world. If there is a discrepancy it will then prompt the user and ask which way to sync. Since all converters are bidirectional it is capable of syncing changes both ways.
Next, Air iterates through the world and runs the converters on each file again, this time checking to see if their would-be output exists in the development directory. If not, the file is new and the output is written. There is no need to bother with the case where the output exists since we know it is already correct due to the previous operation.

Air then monitors both directories for changes and syncs them as soon as they are detected. It is intended to be run in the background during development so that you simply save in the development directory and the world is updated automatically.

## MCJson
MCJson is a custom, YAML-inspired syntax specifically designed to simplify working with the types of `.json` files Minecraft uses.
```
# this is a comment
this_is_a_key
  # everything within a key is indented (although comments don't have to be)
  
  # keys and values are space separated
  key value
  # values fall back to strings, but numbers, `true` and `false` are parsed first
  age 24
  employed true
  # if a string value contains a space it should be wrapped in double quotes
  example "like this"
  
  # values can also be lists of simple values with optional commas
  fruits [ apple, peach, pear ]
  prices [ 3 -4.7 5.0 ]
  # or simple blocks, which require commas
  filters { test has_damage, value magic }
 
  # for more complex lists, a dash syntax is used
  complex_list_key
    - I_am_a_string_value
    - "I am also a string value"
    - this "is a block value"
      which "can have multiple keys"
```
