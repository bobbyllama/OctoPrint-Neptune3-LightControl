/* global OCTOPRINT_VIEWMODELS, OctoPrint, $, ko */
$(function () {
  function LightControlViewModel(parameters) {
    var self = this;
    self.loginState = parameters[0];
    self.printerState = parameters[1];

    self.isOn = ko.observable(null); // unknown initially
    self.isBusy = ko.observable(false);

    // PWM value 0..255, shown in a 3-char field
    self.pwmValue = ko.observable("255");

    // sanitize input to digits only, length <= 3, clamp 0..255 on send
    self.onPwmInput = function (_, e) {
      var v = (e.target.value || "").replace(/[^\d]/g, "");
      if (v.length > 3) v = v.slice(0, 3);
      e.target.value = v;
      self.pwmValue(v);
      return true;
    };

    function clampPwm(v) {
      var n = parseInt(v, 10);
      if (isNaN(n)) return null;     // treat empty as not provided
      if (n < 0) n = 0;
      if (n > 255) n = 255;
      return n;
    }

    function call(cmd, data) {
      self.isBusy(true);
      return OctoPrint.simpleApiCommand("neptune3_lightcontrol", cmd, data || {})
        .done(function (resp) {
          if (resp && typeof resp.is_on !== "undefined") {
            self.isOn(!!resp.is_on);
          } else if (typeof resp.assumed_is_on !== "undefined") {
            self.isOn(!!resp.assumed_is_on);
          }
        })
        .always(function () {
          self.isBusy(false);
        });
    }

    self.toggle = function () {
      var target = self.isOn() === true ? "off" : (self.isOn() === false ? "on" : "toggle");
      var pwm = clampPwm(self.pwmValue());
      var payload = { target: target, pwm: pwm };
      call("toggle", payload);
    };

    self.query = function () { call("query_status", {}); };

    // Query once after load
    setTimeout(self.query, 1500);
  }

  OCTOPRINT_VIEWMODELS.push({
    construct: LightControlViewModel,
    dependencies: ["loginStateViewModel", "printerStateViewModel"],
    elements: ["#navbar_plugin_neptune3_lightcontrol"]
  });
});
