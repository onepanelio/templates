# Template sections

## Generated fields

The following fields will be generated as part of starter template
- machine-type: this parameter is added automatically, is required and its options are grabbed from `onepanel` configmap.
- startup-script: this parameter is added automatically, is optional, the value is used in `lifeCycle.postStart` field.

The following fields will be injected on creation:
- host: this is grabbed from `onepanel` configmap.

