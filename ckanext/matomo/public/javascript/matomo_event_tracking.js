ckan.module("matomo", function(jQuery, _) {
  "use strict";

  return {
     initialize: function() {
      jQuery("a.resource-url-analytics").on("click", function() {

        let resource_url = encodeURIComponent(jQuery(this).prop("href"));
        if (resource_url) {
          _paq.push(["trackEvent", "Resource", "Open", resource_url]);
        }
      });
    }
  };
});

