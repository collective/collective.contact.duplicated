var contactduplicated = {};
contactduplicated.merge_contacts = function () {
    var uids = contactfacetednav.contacts.selection_uids();
    var baseURL = $('body').data('baseUrl') // plone 5
    if (!baseURL) {
        baseURL = $('base').attr('href'); // plone 4
    }
    var params = contactfacetednav.serialize_uids(uids)
    window.location.href = baseURL + '/merge-contacts?' + params;
};
