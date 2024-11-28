from string import Template

_CLEAN_LOCAL_FILE_PROMPT = """{
  "6": {
    "inputs": {
      "type": "$type",
      "path": "$path"
    },
    "class_type": "Clean input and output file",
    "_meta": {
      "title": "file_cleaner"
    }
  }
}"""

CLEAN_LOCAL_FILE_PROMPT_TEMPLATE = Template(_CLEAN_LOCAL_FILE_PROMPT)
