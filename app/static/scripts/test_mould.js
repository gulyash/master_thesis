$(".btn-test-mouldside").click(function () {
    // get id of the button
    let sideName = this.id;
    // make sure the first letter is upper case
    sideName = sideName.charAt(0).toUpperCase() + sideName.slice(1);
    // move to test endpoint
    window.location = '/test-mould/side?mold_side=' + sideName;
});