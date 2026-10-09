*** Settings ***
Documentation  collective.contact.duplicated keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Robot Framework 3.0 syntax (shared with the Plone 4.3 environment).
...            Fixture: collective.contact.core test data (mydirectory: persons degaulle, pepper, held positions).
...            Selectors: this package (compare.pt) and collective.contact.facetednav.
Resource  ui_plone${PLONE_MAJOR}.robot


*** Variables ***
${DIRECTORY_URL}  ${PLONE_URL}/mydirectory
${MERGE_FORM}  css=#form
${MERGE_ACTION}  css=#contact-facetednav-action-merge


*** Keywords ***
Open a manager browser
    Open test browser
    Set window size  1280  2000
    Enable autologin as  Manager

Uid of
    [Documentation]  uid of a content of mydirectory, by path (e.g. degaulle/adt)
    [Arguments]  ${path}
    ${uid}=  Path to uid  /${PLONE_SITE_ID}/mydirectory/${path}
    [Return]  ${uid}

Open the merge page of
    [Arguments]  ${path1}  ${path2}
    ${uid1}=  Uid of  ${path1}
    ${uid2}=  Uid of  ${path2}
    Go to  ${DIRECTORY_URL}/merge-contacts?uids:list=${uid1}&uids:list=${uid2}
    Wait until page contains element  ${MERGE_FORM}

The field values differ
    [Documentation]  the field row shows the values of the two contents as differing
    [Arguments]  ${field}  ${value1}  ${value2}
    Page should contain element  xpath=//label[@class="differing" and starts-with(@for, "${field}-") and normalize-space(.)="${value1}"]
    Page should contain element  xpath=//label[@class="differing" and starts-with(@for, "${field}-") and normalize-space(.)="${value2}"]

The persons can be merged too
    Page should contain element  css=#hp-person-merge input[name="merge-hp-persons"]
    Checkbox should be selected  css=#hp-person-merge input[name="merge-hp-persons"]

Merge the contents
    Click button  ${MERGE_FORM} input[type="submit"]

The merge page is open
    [Documentation]  the facetednav url is mydirectory//merge-contacts?uids%3Alist=...
    Wait until location contains  merge-contacts?
    Wait until page contains element  ${MERGE_FORM}

The kept content is
    [Arguments]  ${path}
    Location should be  ${DIRECTORY_URL}/${path}

The content is removed
    [Arguments]  ${path}
    Go to  ${DIRECTORY_URL}/${path}
    The page is not found

Open the faceted directory
    Go to  ${DIRECTORY_URL}
    Wait until page contains element  ${MERGE_ACTION}
    # contacts of the results loaded by collective.contact.facetednav
    Wait for condition  return typeof contactfacetednav.contacts !== 'undefined' && contactfacetednav.contacts.length > 0

Select the contact
    [Arguments]  ${path}
    ${uid}=  Uid of  ${path}
    Select checkbox  css=#contact-${uid}

Click the merge action
    Wait until element is enabled  ${MERGE_ACTION}
    Click button  ${MERGE_ACTION}
