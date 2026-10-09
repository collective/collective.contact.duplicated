*** Settings ***
Documentation  "Merge duplicated" batch action of the collective.contact.facetednav faceted directory.
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  duplicated.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Test Cases ***
The merge action opens the merge page of the selected contacts
    Open the faceted directory
    Select the contact  degaulle
    Select the contact  pepper
    Click the merge action
    The merge page is open
    The field values differ  lastname  De Gaulle  Pepper
