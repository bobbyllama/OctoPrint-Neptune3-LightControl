# -*- coding: utf-8 -*-
from __future__ import absolute_import
import octoprint.plugin
from flask import jsonify, request, make_response

PLUGIN_IDENTIFIER = "neptune3_lightcontrol"
DEFAULTS = {
    "gcode_on": "M355 S1",    # Supports '{p}' token, e.g. "M355 S1 P{p}"
    "gcode_off": "M355 S0",
    "gcode_toggle": "",
    "status_query": "",
    "status_parse_token": ""
}

def _parse_pwm(value):
    """Return int 0..255 or None if invalid/absent."""
    try:
        if value is None or value == "":
            return None
        n = int(value)
        if n < 0:
            n = 0
        if n > 255:
            n = 255
        return n
    except Exception:
        return None

class Neptune3LightControlPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SimpleApiPlugin,
):
    def __init__(self):
        self._is_on = None

    # --- OctoPrint Hooks ---
    def get_settings_defaults(self):
        return DEFAULTS.copy()

    def get_assets(self):
        return dict(js=["js/lightcontrol.js"], css=["css/lightcontrol.css"])

    def get_template_configs(self):
        # Navbar button + input
        return [dict(type="navbar", name="Light", data_bind="visible: loginState.hasPermission('CONTROL')")]

    def on_after_startup(self):
        self._logger.info("Neptune3 LightControl loaded. on=%r off=%r toggle=%r",
                          self._settings.get(["gcode_on"]),
                          self._settings.get(["gcode_off"]),
                          self._settings.get(["gcode_toggle"]))
        self._query_status_async()

    # --- Simple API ---
    def get_api_commands(self):
        # pwm is optional and only used when turning ON (or explicit 'on' target)
        return dict(toggle=["target", "pwm"], set_state=["state", "pwm"], query_status=[])

    def on_api_command(self, command, data):
        if command == "toggle":
            target = data.get("target", "toggle")
            pwm = _parse_pwm(data.get("pwm"))
            return make_response(jsonify(self._handle_toggle(target, pwm)), 200)

        if command == "set_state":
            state = str(data.get("state", "")).lower()
            if state not in ("on", "off"):
                return make_response(jsonify(dict(ok=False, error="state must be 'on' or 'off'")), 400)
            pwm = _parse_pwm(data.get("pwm"))
            return make_response(jsonify(self._handle_set(state, pwm)), 200)

        if command == "query_status":
            ok, is_on = self._query_status()
            return make_response(jsonify(dict(ok=ok, is_on=is_on)), 200)

        return make_response(jsonify(dict(ok=False, error="unknown command")), 400)

    # --- Actions ---
    def _handle_toggle(self, target, pwm=None):
        if target == "toggle":
            g_toggle = self._settings.get(["gcode_toggle"]) or ""
            if g_toggle.strip():
                self._send_gcode_lines([g_toggle])
                self._is_on = not bool(self._is_on) if self._is_on is not None else None
                return dict(ok=True, assumed_is_on=self._is_on, used="toggle")
            else:
                next_state = "off" if self._is_on else "on"
                return self._handle_set(next_state, pwm)

        if target in ("on", "off"):
            return self._handle_set(target, pwm)

        return dict(ok=False, error="bad target")

    def _handle_set(self, state, pwm=None):
        if state == "on":
            cmd = (self._settings.get(["gcode_on"]) or "").strip()

            # If caller provided PWM, try to inject it.
            if pwm is not None:
                # Token replacement first
                if "{p}" in cmd.lower():
                    # Case-insensitive replace: rebuild using find
                    # Simple approach: replace all case variations by formatting lower
                    # We'll just do a case-insensitive swap:
                    import re
                    cmd = re.sub(r"{p}", str(pwm), cmd, flags=re.IGNORECASE)
                else:
                    up = cmd.upper()
                    if "M355" in up and "S1" in up and " P" not in up:
                        cmd = cmd + " P{}".format(pwm)

            self._send_gcode_lines([cmd])
            self._is_on = True
            return dict(ok=True, is_on=True, used="on", sent=cmd)

        if state == "off":
            cmd = (self._settings.get(["gcode_off"]) or "").strip()
            self._send_gcode_lines([cmd])
            self._is_on = False
            return dict(ok=True, is_on=False, used="off", sent=cmd)

        return dict(ok=False, error="unknown state")

    def _send_gcode_lines(self, lines):
        if not lines:
            return
        if self._printer is None:
            self._logger.warn("No printer interface available to send GCODE.")
            return
        for l in lines:
            l = (l or "").strip()
            if not l:
                continue
            self._logger.debug("Sending GCODE: %s", l)
            try:
                self._printer.commands(l)
            except Exception as e:
                self._logger.error("Failed to send GCODE '%s': %s", l, e)

    # --- Status Query (optional) ---
    def _query_status_async(self):
        try:
            self._logger.debug("Scheduling initial status query")
            self._query_status()
        except Exception:
            pass

    def _query_status(self):
        q = (self._settings.get(["status_query"]) or "").strip()
        token = (self._settings.get(["status_parse_token"]) or "").strip()
        if not q:
            return False, self._is_on
        self._send_gcode_lines([q])
        self._logger.info("Sent status query '%s'. Configure 'status_parse_token' if you add a serial hook.", q)
        return True, self._is_on


__plugin_name__ = "Neptune3 Light Control"
__plugin_pythoncompat__ = ">=3.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Neptune3LightControlPlugin()

def __plugin_hooks__():
    return {
        "octoprint.plugin.softwareupdate.check_config":
            lambda: dict(
                neptune3_lightcontrol=dict(
                    displayName="Neptune3 Light Control",
                    displayVersion="1.1.0",
                    type="github_release",
                    user="bobbyllama",
                    repo="OctoPrint-Neptune3-LightControl",
                    current="1.1.0",
                )
            )
    }
