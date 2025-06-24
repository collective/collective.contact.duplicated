var contactduplicated = {};
contactduplicated.merge_contacts = function(){
    var uids = contactfacetednav.contacts.selection_uids();
    var base_url = $('body').data('base-url');
    var params = contactfacetednav.serialize_uids(uids)
    window.location.href = base_url + '/merge-contacts?' + params;
};
