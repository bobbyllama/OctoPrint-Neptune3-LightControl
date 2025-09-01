# -*- coding: utf-8 -*-
from setuptools import setup

plugin_identifier = "neptune3_lightcontrol"
plugin_package = "octoprint_" + plugin_identifier
plugin_name = "Neptune3 Light Control"
plugin_version = "1.0.0"
plugin_description = "Navbar button to toggle the Neptune 3's light with configurable G-code."
plugin_author = "Bobby (with a little help)"
plugin_license = "MIT"
plugin_url = "https://github.com/bobbyllama/OctoPrint-Neptune3-LightControl"

requires = []

additional_data = [
    "templates/*.*",
    "templates/**/*.*",
    "static/*.*",
    "static/**/*.*",
]

setup(
    name="OctoPrint-{}".format(plugin_identifier.replace("_", "-")),
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    license=plugin_license,
    url=plugin_url,
    packages=[plugin_package],
    package_dir={plugin_package: "octoprint_" + plugin_identifier},
    include_package_data=True,
    install_requires=requires,
    entry_points={
        "octoprint.plugin": [
            "{} = {}:{}".format(plugin_identifier, plugin_package, "Neptune3LightControlPlugin")
        ]
    },
    zip_safe=False,
    cmdclass={},
    package_data={plugin_package: additional_data},
)
