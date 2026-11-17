*** Settings ***
Documentation  Merge duplicated contacts of a directory (merge-contacts and merge-contacts-apply views).
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  duplicated.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Test Cases ***
The merge page compares two persons
    Open the merge page of  degaulle  pepper
    The field values differ  lastname  De Gaulle  Pepper
    The field values differ  city  Colombey les deux églises  Liverpool
    Page should contain  /plone/mydirectory/degaulle
    Page should contain  /plone/mydirectory/pepper

Merging two persons keeps the selected one
    Open the merge page of  degaulle  pepper
    Merge the contents
    The kept content is  degaulle
    The status message contains  /plone/mydirectory/pepper has been removed
    The content is removed  pepper

Merging held positions of different persons leads to the merge of the persons
    Open the merge page of  degaulle/adt  pepper/sergent_pepper
    The persons can be merged too
    Merge the contents
    The merge page is open
    The field values differ  lastname  De Gaulle  Pepper
