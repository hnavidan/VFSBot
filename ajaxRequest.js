return $.ajax({
    type: 'POST',
    url: '/Global-Appointment/Account/CheckSeatAllotment',
    headers: headers,
    dataType: 'JSON',
    async: false,
    data: {
            // while navigating to the VFS appointment page
            // open the network tab in the developer tools in your browser
            // and submit the form then copy the values from the request payload
            countryId: "44",
            missionId: "14",
            LocationId: "248",
            Location: "Centre d’application pour le Portugal, Rabat"
    },
    cache: false,
    success: function (data) {
        if (data != "") {
            $("#LocationError").text(data);
            $("#btnContinue").attr("disabled", true);
            $("#btnContinue").removeClass("EnableButton");
            $("#btnContinue").addClass("DisabledButton");
            $(".drpVisaCategory").prop("disabled", true);
        }
        else {
            $(".drpVisaCategory").prop("disabled", false);
        }
        return data
    }
}).responseJSON;