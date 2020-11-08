===========================
 sopel-lookoutside
=========================== 

Introduction
============
sopel-lookoutside is a weather lookup plugin for Sopel.

Why another weather modules? Because I wanted to add a few features and provide more granular control over output per user.

Changes from sopel-weather:
 - removed darksky option as they have closed API registration
 - added Air Quality Index reports from airnow.gov (US)
 - added .weatherset configuration, allowing users to choose how to display their weather


Installing
==========

If possible, use ``pip`` to install this plugin. Below are example commands; you
might need to add ``sudo`` and/or call a different ``pip`` (e.g. ``pip3``) depending
on your system and environment. Do not use ``setup.py install``; Sopel won't be
able to load the plugin correctly.


From source
~~~~~~~~~~~
Clone the repo, then run this in /path/to/sopel-lookoutside

.. code-block::

    pip install .

Configuring
===========
You can automatically configure this plugin using the `sopel configure --plugins` command.

However, if you want or need to configure this plugin manually, you will need to define the following in `~/.sopel/default.cfg`

.. code-block::

    [weather]
    geocoords_provider = GEOCOORDS_PROVIDER
    geocoords_api_key = GEOCOORDS_API_KEY
    weather_provider = WEATHER_PROVIDER
    weather_api_key = WEATHER_API_KEY
    airnow_api_key = AIRNOW_API_KEY



Usage
=====

Current Weather
~~~~~~~~~~~~~~~
.. code-block::

    .weather # Only works if setlocation has been previously run
    .weather seattle, us
    .weather london

.. code-block::

    Paris, Ile-de-France, FR: 6°C (42°F), Clear, Humidity: 83%, UV Index: 0, Gentle breeze 4.0m/s (↗)

4day Forecast
~~~~~~~~~~~~~~
.. code-block::

    .forecast # Only works if setlocation has been previously run
    .forecast seattle, us
    .forecast london

.. code-block::

 Forecast: Paris, Ile-de-France, FR: Light rain tomorrow through next Saturday, High: 15°C (59°F), Low: 11°C (52°F), UV Index: 2

Air Quality Index
~~~~~~~~~~~~~~~~~~~

.. code-block::

    .aqi # Only works if setlocation has been previously run
    .aqi seattle, us
    .aqi 90029

.. code-block::

    Seattle-Bellevue-Kent Valley, WA:  O3 Good (AQI: 17) PM2.5 Good (AQI: 38)

User Customizations
~~~~~~~~~~~~~~~~~~~~~~~
.. code-block::

    .weatherset units [metric|imperial|both]
    .weatherset [condition|humidity|sunrise|wind|aqi] [true|false]

.. code-block::

    Preference set units: imperial

Requirements
============

Modern weather APIs require Latitude & Longitude as inputs to their APIs, so we need to leverage a GeoCoords API to convert location searches to coordinates.

API Keys
~~~~~~~~

GeoCoords
*********
LocationIQ

.. code-block::

    https://locationiq.com/

Weather
*******
OpenWeatherMap

.. code-block::

    https://openweathermap.org/

Python Requirements
~~~~~~~~~~~~~~~~~~~
.. code-block::

    requests
    sopel
    pytz

