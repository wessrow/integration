"""SL Platform Sensor"""

import logging
import math
import datetime

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.util.dt import now

from .const import (
    CONF_DESTINATION_ID,
    CONF_RR_KEY,
    CONF_SOURCE_ID,
    DOMAIN,
    HASL_VERSION,
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_GUID,
    SENSOR_RRARR,
    SENSOR_RRDEP,
    SENSOR_RRROUTE,
    SENSOR_STANDARD,
    SENSOR_STATUS,
    SENSOR_VEHICLE_LOCATION,
    SENSOR_DEVIATION,
    SENSOR_ROUTE,
    CONF_ANALOG_SENSORS,
    CONF_FP_PT,
    CONF_FP_RB,
    CONF_FP_TVB,
    CONF_FP_SB,
    CONF_FP_LB,
    CONF_FP_SPVC,
    CONF_FP_TB1,
    CONF_FP_TB2,
    CONF_TL2_KEY,
    CONF_RI4_KEY,
    CONF_SI2_KEY,
    CONF_RP3_KEY,
    CONF_SITE_ID,
    CONF_SENSOR,
    CONF_LINES,
    CONF_INTEGRATION_TYPE,
    CONF_INTEGRATION_ID,
    CONF_DEVIATION_LINES,
    CONF_DEVIATION_STOPS,
    CONF_DEVIATION_LINE,
    CONF_DEVIATION_STOP,
    CONF_SENSOR_PROPERTY,
    CONF_DIRECTION,
    CONF_TIMEWINDOW,
    CONF_SCAN_INTERVAL,
    CONF_SOURCE,
    CONF_DESTINATION,
    STATE_ON,
    CONF_TRANSPORT_MODE_LIST,
)

logger = logging.getLogger(f"custom_components.{DOMAIN}.sensors")


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities(await setup_hasl_sensor(hass, config))


async def async_setup_entry(hass, config_entry, async_add_devices):
    async_add_devices(await setup_hasl_sensor(hass, config_entry))


async def setup_hasl_sensor(hass, config):
    """Setup sensor platform."""
    logger.debug("[setup_hasl_sensor] Entered")

    sensors = []
    worker = hass.data[DOMAIN]["worker"]

    try:
        logger.debug("[setup_hasl_sensor] Setting up RI4 sensors...")
        if config.data[CONF_INTEGRATION_TYPE] == SENSOR_STANDARD:
            if CONF_RI4_KEY in config.data and CONF_SITE_ID in config.data:
                await worker.assert_ri4(
                    config.data[CONF_RI4_KEY], config.data[CONF_SITE_ID]
                )
                sensors.append(
                    HASLDepartureSensor(hass, config, config.data[CONF_SITE_ID])
                )
            logger.debug("[setup_hasl_sensor] Force processing RI4 sensors")
            await worker.process_ri4()
        logger.debug("[setup_hasl_sensor] Completed setting up RI4 sensors")
    except Exception as e:
        logger.error(f"[setup_hasl_sensor] Failed to set up RI4 sensors: {str(e)}")

    try:
        logger.debug("[setup_hasl_sensor] Setting up SI2 sensors...")
        if config.data[CONF_INTEGRATION_TYPE] == SENSOR_DEVIATION:
            if CONF_SI2_KEY in config.data:
                for deviationid in ",".join(
                    set(config.data[CONF_DEVIATION_LINES].split(","))
                ).split(","):
                    await worker.assert_si2_line(config.data[CONF_SI2_KEY], deviationid)
                    sensors.append(
                        HASLDeviationSensor(
                            hass, config, CONF_DEVIATION_LINE, deviationid
                        )
                    )
                for deviationid in ",".join(
                    set(config.data[CONF_DEVIATION_STOPS].split(","))
                ).split(","):
                    await worker.assert_si2_stop(config.data[CONF_SI2_KEY], deviationid)
                    sensors.append(
                        HASLDeviationSensor(
                            hass, config, CONF_DEVIATION_STOP, deviationid
                        )
                    )
            logger.debug("[setup_hasl_sensor] Force processing SI2 sensors")
            await worker.process_si2()
        logger.debug("[setup_hasl_sensor] Completed setting up SI2 sensors")
    except Exception as e:
        logger.error(f"[setup_hasl_sensor] Failed to set up SI2 sensors: {str(e)}")

    try:
        logger.debug("[setup_hasl_sensor] Setting up RP3 sensors...")
        if config.data[CONF_INTEGRATION_TYPE] == SENSOR_ROUTE:
            if CONF_RP3_KEY in config.data:
                await worker.assert_rp3(
                    config.data[CONF_RP3_KEY],
                    config.data[CONF_SOURCE],
                    config.data[CONF_DESTINATION],
                )
                sensors.append(
                    HASLRouteSensor(
                        hass,
                        config,
                        f"{config.data[CONF_SOURCE]}-{config.data[CONF_DESTINATION]}",
                    )
                )
            logger.debug("[setup_hasl_sensor] Force processing RP3 sensors")
            await worker.process_rp3()
        logger.debug("[setup_hasl_sensor] Completed setting up RP3 sensors")
    except Exception as e:
        logger.error(f"[setup_hasl_sensor] Failed to set up RP3 sensors: {str(e)}")

    try:
        logger.debug("[setup_hasl_sensor] Setting up TL2 sensors...")
        if config.data[CONF_INTEGRATION_TYPE] == SENSOR_STATUS:
            if CONF_ANALOG_SENSORS in config.data:
                if CONF_TL2_KEY in config.data:
                    await worker.assert_tl2(config.data[CONF_TL2_KEY])

                    for sensortype in CONF_TRANSPORT_MODE_LIST:
                        if sensortype in config.data and config.data[sensortype]:
                            sensors.append(
                                HASLTrafficStatusSensor(hass, config, sensortype)
                            )

                logger.debug("[setup_hasl_sensor] Force processing TL2 sensors")
                await worker.process_tl2()
        logger.debug("[setup_hasl_sensor] Completed setting up TL2 sensors")
    except Exception as e:
        logger.error(f"[setup_hasl_sensor] Failed to set up TL2 sensors: {str(e)}")

    try:
        logger.debug("[setup_hasl_sensor] Setting up FP sensors...")
        if config.data[CONF_INTEGRATION_TYPE] == SENSOR_VEHICLE_LOCATION:
            if CONF_FP_PT in config.data and config.data[CONF_FP_PT]:
                await worker.assert_fp("PT")
                sensors.append(HASLVehicleLocationSensor(hass, config, "PT"))
            if CONF_FP_RB in config.data and config.data[CONF_FP_RB]:
                await worker.assert_fp("RB")
                sensors.append(HASLVehicleLocationSensor(hass, config, "RB"))
            if CONF_FP_TVB in config.data and config.data[CONF_FP_TVB]:
                await worker.assert_fp("TVB")
                sensors.append(HASLVehicleLocationSensor(hass, config, "TVB"))
            if CONF_FP_SB in config.data and config.data[CONF_FP_SB]:
                await worker.assert_fp("SB")
                sensors.append(HASLVehicleLocationSensor(hass, config, "SB"))
            if CONF_FP_LB in config.data and config.data[CONF_FP_LB]:
                await worker.assert_fp("LB")
                sensors.append(HASLVehicleLocationSensor(hass, config, "LB"))
            if CONF_FP_SPVC in config.data and config.data[CONF_FP_SPVC]:
                await worker.assert_fp("SpvC")
                sensors.append(HASLVehicleLocationSensor(hass, config, "SpvC"))
            if CONF_FP_TB1 in config.data and config.data[CONF_FP_TB1]:
                await worker.assert_fp("TB1")
                sensors.append(HASLVehicleLocationSensor(hass, config, "TB1"))
            if CONF_FP_TB2 in config.data and config.data[CONF_FP_TB2]:
                await worker.assert_fp("TB2")
                sensors.append(HASLVehicleLocationSensor(hass, config, "TB2"))
            if CONF_FP_TB2 in config.data and config.data[CONF_FP_TB2]:
                await worker.assert_fp("TB3")
                sensors.append(HASLVehicleLocationSensor(hass, config, "TB3"))
            logger.debug("[setup_hasl_sensor] Force processing FP sensors")
            await worker.process_fp()
        logger.debug("[setup_hasl_sensor] Completed setting up FP sensors")
    except Exception as e:
        logger.error(f"[setup_hasl_sensor] Failed to set up FP sensors: {str(e)}")

    try:
        logger.debug("[setup_hasl_sensor] Setting up RRD sensors...")
        if config.data[CONF_INTEGRATION_TYPE] == SENSOR_RRDEP:
            if CONF_RR_KEY in config.data and CONF_SITE_ID in config.data:
                await worker.assert_rrd(
                    config.data[CONF_RR_KEY], config.data[CONF_SITE_ID]
                )
                sensors.append(
                    HASLRRDepartureSensor(hass, config, config.data[CONF_SITE_ID])
                )
            logger.debug("[setup_hasl_sensor] Force processing RRD sensors")
            await worker.process_rrd(hass)
        logger.debug("[setup_hasl_sensor] Completed setting up RRD sensors")
    except Exception as e:
        logger.error(f"[setup_hasl_sensor] Failed to set up RRD sensors: {str(e)}")

    try:
        logger.debug("[setup_hasl_sensor] Setting up RRA sensors...")
        if config.data[CONF_INTEGRATION_TYPE] == SENSOR_RRARR:
            if CONF_RR_KEY in config.data and CONF_SITE_ID in config.data:
                await worker.assert_rra(
                    config.data[CONF_RR_KEY], config.data[CONF_SITE_ID]
                )
                sensors.append(
                    HASLRRArrivalSensor(hass, config, config.data[CONF_SITE_ID])
                )
            logger.debug("[setup_hasl_sensor] Force processing RRA sensors")
            await worker.process_rra(hass)
        logger.debug("[setup_hasl_sensor] Completed setting up RRA sensors")
    except Exception as e:
        logger.error(f"[setup_hasl_sensor] Failed to set up RRA sensors: {str(e)}")

    # try:
    logger.debug("[setup_hasl_sensor] Setting up RRR sensors...")
    if config.data[CONF_INTEGRATION_TYPE] == SENSOR_RRROUTE:
        if CONF_RR_KEY in config.data:
            await worker.assert_rrr(
                config.data[CONF_RR_KEY],
                config.data[CONF_SOURCE_ID],
                config.data[CONF_DESTINATION_ID],
            )
            sensors.append(
                HASLRRRouteSensor(
                    hass,
                    config,
                    f"{config.data[CONF_SOURCE_ID]}-{config.data[CONF_DESTINATION_ID]}",
                )
            )
        logger.debug("[setup_hasl_sensor] Force processing RRR sensors")
        await worker.process_rrr()
    logger.debug("[setup_hasl_sensor] Completed setting up RRR sensors")
    # except Exception as e:
    #    logger.error(f"[setup_hasl_sensor] Failed to set up RRR sensors: {str(e)}")

    logger.debug("[setup_hasl_sensor] Completed")
    return sensors


class HASLDevice(Entity):
    """HASL Device class."""

    @property
    def device_info(self):
        """Return device information about HASL Device."""
        return {
            "identifiers": {(DOMAIN, DEVICE_GUID)},
            "name": DEVICE_NAME,
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL,
            "sw_version": HASL_VERSION,
            "entry_type": DeviceEntryType.SERVICE,
        }


class HASLRouteSensor(HASLDevice):
    """HASL Train Location Sensor class."""

    def __init__(self, hass, config, trip):
        """Initialize."""
        self._hass = hass
        self._config = config
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._trip = trip
        self._name = f"SL {self._trip} Route Sensor ({self._config.title})"
        self._sensordata = []
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")

        if self._worker.data.rp3[self._trip]["api_lastrun"]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.rp3[self._trip]["api_lastrun"],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                ):
                    try:
                        await self._worker.process_rp3()
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")

        self._sensordata = self._worker.data.rp3[self._trip]
        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-route-{self._trip}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return "Unknown"
        else:
            return len(self._sensordata["trips"])

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        return self._sensordata != []

    @property
    def extra_state_attributes(self):
        val = {}

        if self._sensordata == []:
            return val

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Success"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )
        try:
            val["attribution"] = self._sensordata["attribution"]
            val["trips"] = self._sensordata["trips"]
            val["transfers"] = self._sensordata["transfers"]
            val["price"] = self._sensordata["price"]
            val["time"] = self._sensordata["time"]
            val["duration"] = self._sensordata["duration"]
            val["to"] = self._sensordata["to"]
            val["from"] = self._sensordata["from"]
            val["origin"] = {}
            val["origin"]["leg"] = self._sensordata["origin"]["leg"]
            val["origin"]["line"] = self._sensordata["origin"]["line"]
            val["origin"]["direction"] = self._sensordata["origin"]["direction"]
            val["origin"]["category"] = self._sensordata["origin"]["category"]
            val["origin"]["time"] = self._sensordata["origin"]["time"]
            val["origin"]["from"] = self._sensordata["origin"]["from"]
            val["origin"]["to"] = self._sensordata["origin"]["to"]
            val["origin"]["prognosis"] = self._sensordata["origin"]["prognosis"]
            val["destination"] = {}
            val["destination"]["leg"] = self._sensordata["destination"]["leg"]
            val["destination"]["line"] = self._sensordata["destination"]["line"]
            val["destination"]["direction"] = self._sensordata["destination"][
                "direction"
            ]
            val["destination"]["category"] = self._sensordata["destination"]["category"]
            val["destination"]["time"] = self._sensordata["destination"]["time"]
            val["destination"]["from"] = self._sensordata["destination"]["from"]
            val["destination"]["to"] = self._sensordata["destination"]["to"]
            val["destination"]["prognosis"] = self._sensordata["destination"][
                "prognosis"
            ]
            val["last_refresh"] = self._sensordata["last_updated"]
            val["trip_count"] = len(self._sensordata["trips"])
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val


class HASLRRRouteSensor(HASLDevice):
    """HASL Train Location Sensor class."""

    def __init__(self, hass, config, trip):
        """Initialize."""
        self._hass = hass
        self._config = config
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._trip = trip
        self._name = f"RR {self._trip} Route Sensor ({self._config.title})"
        self._sensordata = []
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")

        if self._worker.data.rrr[self._trip]["api_lastrun"]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.rrr[self._trip]["api_lastrun"],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                ):
                    try:
                        await self._worker.process_rrr()
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")

        self._sensordata = self._worker.data.rrr[self._trip]
        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"rr-route-{self._trip}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return "Unknown"
        else:
            return len(self._sensordata["trips"])

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        return self._sensordata != []

    @property
    def extra_state_attributes(self):
        val = {}

        if self._sensordata == []:
            return val

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Success"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )
        try:
            val["attribution"] = self._sensordata["attribution"]
            val["trips"] = self._sensordata["trips"]
            val["transfers"] = self._sensordata["transfers"]
            val["time"] = self._sensordata["time"]
            val["duration"] = self._sensordata["duration"]
            val["to"] = self._sensordata["to"]
            val["from"] = self._sensordata["from"]
            val["origin"] = {}
            val["origin"]["leg"] = self._sensordata["origin"]["leg"]
            val["origin"]["line"] = self._sensordata["origin"]["line"]
            val["origin"]["direction"] = self._sensordata["origin"]["direction"]
            val["origin"]["category"] = self._sensordata["origin"]["category"]
            val["origin"]["time"] = self._sensordata["origin"]["time"]
            val["origin"]["from"] = self._sensordata["origin"]["from"]
            val["origin"]["to"] = self._sensordata["origin"]["to"]
            val["origin"]["prognosis"] = self._sensordata["origin"]["prognosis"]
            val["destination"] = {}
            val["destination"]["leg"] = self._sensordata["destination"]["leg"]
            val["destination"]["line"] = self._sensordata["destination"]["line"]
            val["destination"]["direction"] = self._sensordata["destination"][
                "direction"
            ]
            val["destination"]["category"] = self._sensordata["destination"]["category"]
            val["destination"]["time"] = self._sensordata["destination"]["time"]
            val["destination"]["from"] = self._sensordata["destination"]["from"]
            val["destination"]["to"] = self._sensordata["destination"]["to"]
            val["destination"]["prognosis"] = self._sensordata["destination"][
                "prognosis"
            ]
            val["last_refresh"] = self._sensordata["last_updated"]
            val["trip_count"] = len(self._sensordata["trips"])
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val


class HASLDepartureSensor(HASLDevice):
    """HASL Departure Sensor class."""

    def __init__(self, hass, config, siteid):
        """Initialize."""

        unit_table = {
            "min": "min",
            "time": "",
            "deviations": "",
            "updated": "",
        }

        self._hass = hass
        self._config = config
        self._lines = config.data[CONF_LINES]
        self._siteid = str(siteid)
        self._name = f"SL Departure Sensor {self._siteid} ({self._config.title})"
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._sensorproperty = config.data[CONF_SENSOR_PROPERTY]
        self._direction = config.data[CONF_DIRECTION]
        self._timewindow = config.data[CONF_TIMEWINDOW]
        self._nextdeparture_minutes = "0"
        self._nextdeparture_expected = "-"
        self._lastupdate = "-"
        self._unit_of_measure = unit_table.get(
            self._config.data[CONF_SENSOR_PROPERTY], "min"
        )
        self._sensordata = None
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

        if self._lines == "":
            self._lines = []
        if not isinstance(self._lines, list):
            self._lines = self._lines.split(",")

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")
        if self._worker.data.ri4[self._siteid]["api_lastrun"]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.ri4[self._siteid]["api_lastrun"],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                ):
                    try:
                        await self._worker.process_ri4()
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")

        self._sensordata = self._worker.data.ri4[self._siteid]

        logger.debug("[async_update] Performing calculations")
        if f"stop_{self._siteid}" in self._worker.data.si2:
            if "data" in self._worker.data.si2[f"stop_{self._siteid}"]:
                self._sensordata["deviations"] = self._worker.data.si2[
                    f"stop_{self._siteid}"
                ]["data"]
            else:
                self._sensordata["deviations"] = []
        else:
            self._sensordata["deviations"] = []

        if "last_updated" in self._sensordata:
            self._last_updated = self._sensordata["last_updated"]
        else:
            self._last_updated = now().strftime("%Y-%m-%d %H:%M:%S")

        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-stop-{self._siteid}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        sensorproperty = self._config.data[CONF_SENSOR_PROPERTY]

        if self._sensordata == []:
            return "Unknown"

        if sensorproperty == "min":
            next_departure = self.nextDeparture()
            if not next_departure:
                return "-"

            delta = next_departure["expected"] - datetime.datetime.now()
            expected_minutes = math.floor(delta.total_seconds() / 60)
            return expected_minutes

        # If the sensor should return the time at which next departure occurs.
        if sensorproperty == "time":
            next_departure = self.nextDeparture()
            if not next_departure:
                return "-"

            expected = next_departure["expected"].strftime("%H:%M:%S")
            return expected

        # If the sensor should return the number of deviations.
        if sensorproperty == "deviations":
            return len(self._sensordata["deviations"])

        if sensorproperty == "updated":
            return self._sensordata["last_updated"]

        # Fail-safe
        return "-"

    def nextDeparture(self):
        if not self._sensordata:
            return None

        now = datetime.datetime.now()
        if "data" in self._sensordata:
            for departure in self._sensordata["data"]:
                if departure["expected"] > now:
                    return departure
        return None

    def filter_direction(self, departure):
        if self._direction == 0:
            return True
        return departure["direction"] == self._direction

    def filter_lines(self, departure):
        if not self._lines or len(self._lines) == 0:
            return True
        return departure["line"] in self._lines

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measure

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        if self._sensordata == [] or self._sensordata is None:
            return False
        else:
            return True

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes ."""

        # Initialize the state attributes.

        val = {}

        if self._sensordata == [] or self._sensordata is None:
            return val

        # Format the next expected time.
        next_departure = self.nextDeparture()
        if next_departure:
            expected_time = next_departure["expected"]
            delta = expected_time - datetime.datetime.now()
            expected_minutes = math.floor(delta.total_seconds() / 60)
            expected_time = expected_time.strftime("%H:%M:%S")
        else:
            expected_time = "-"
            expected_minutes = "-"

        # Set up the unit of measure.
        if self._unit_of_measure != "":
            val["unit_of_measurement"] = self._unit_of_measure

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Ok"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )

        if val["api_result"] != "Ok":
            return val

        departures = self._sensordata["data"]
        departures = list(filter(self.filter_direction, departures))
        departures = list(filter(self.filter_lines, departures))

        try:
            val["attribution"] = self._sensordata["attribution"]
            val["departures"] = departures
            val["deviations"] = self._sensordata["deviations"]
            val["last_refresh"] = self._sensordata["last_updated"]
            val["next_departure_minutes"] = expected_minutes
            val["next_departure_time"] = expected_time
            val["deviation_count"] = len(self._sensordata["deviations"])
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val


class HASLRRDepartureSensor(HASLDevice):
    """HASL Departure Sensor class."""

    def __init__(self, hass, config, siteid):
        """Initialize."""

        unit_table = {
            "min": "min",
            "time": "",
            "updated": "",
        }

        self._hass = hass
        self._config = config
        self._lines = config.data[CONF_LINES]
        self._siteid = str(siteid)
        self._name = f"RR Departure Sensor {self._siteid} ({self._config.title})"
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._sensorproperty = config.data[CONF_SENSOR_PROPERTY]
        self._direction = config.data[CONF_DIRECTION]
        self._timewindow = config.data[CONF_TIMEWINDOW]
        self._nextdeparture_minutes = "0"
        self._nextdeparture_expected = "-"
        self._lastupdate = "-"
        self._unit_of_measure = unit_table.get(
            self._config.data[CONF_SENSOR_PROPERTY], "min"
        )
        self._sensordata = None
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

        if self._lines == "":
            self._lines = []
        if not isinstance(self._lines, list):
            self._lines = self._lines.split(",")

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")
        if self._worker.data.rrd[self._siteid]["api_lastrun"]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.rrd[self._siteid]["api_lastrun"],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                ):
                    try:
                        await self._worker.process_rrd(self.hass)
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")

        self._sensordata = self._worker.data.rrd[self._siteid]

        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"rr-departure-{self._siteid}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        sensorproperty = self._config.data[CONF_SENSOR_PROPERTY]

        if self._sensordata == []:
            return "Unknown"

        if sensorproperty == "min":
            next_departure = self.nextDeparture()
            if not next_departure:
                return "-"

            adjustedDateTime = now()
            adjustedDateTime = adjustedDateTime.replace(tzinfo=None)
            delta = next_departure["expected"] - adjustedDateTime
            expected_minutes = math.floor(delta.total_seconds() / 60)
            return expected_minutes

        # If the sensor should return the time at which next departure occurs.
        if sensorproperty == "time":
            next_departure = self.nextDeparture()
            if not next_departure:
                return "-"

            expected = next_departure["expected"].strftime("%H:%M:%S")
            return expected

        if sensorproperty == "updated":
            return self._sensordata["last_updated"]

        # Fail-safe
        return "-"

    def nextDeparture(self):
        if not self._sensordata:
            return None

        adjustedDateTime = now()
        adjustedDateTime = adjustedDateTime.replace(tzinfo=None)
        if "data" in self._sensordata:
            for departure in self._sensordata["data"]:
                if departure["expected"] > adjustedDateTime:
                    return departure
        return None

    def filter_direction(self, departure):
        if self._direction == 0:
            return True
        return departure["direction"] == self._direction

    def filter_lines(self, departure):
        if not self._lines or len(self._lines) == 0:
            return True
        return departure["line"] in self._lines

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measure

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        if self._sensordata == [] or self._sensordata is None:
            return False
        else:
            return True

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes ."""

        # Initialize the state attributes.

        val = {}

        if self._sensordata == [] or self._sensordata is None:
            return val

        # Format the next expected time.
        next_departure = self.nextDeparture()
        if next_departure:
            adjustedDateTime = now()
            adjustedDateTime = adjustedDateTime.replace(tzinfo=None)
            expected_time = next_departure["expected"]
            delta = expected_time - adjustedDateTime
            expected_minutes = math.floor(delta.total_seconds() / 60)
            expected_time = expected_time.strftime("%H:%M:%S")
        else:
            expected_time = "-"
            expected_minutes = "-"

        # Set up the unit of measure.
        if self._unit_of_measure != "":
            val["unit_of_measurement"] = self._unit_of_measure

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Ok"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )

        if val["api_result"] != "Ok":
            return val

        departures = self._sensordata["data"]
        departures = list(filter(self.filter_direction, departures))
        departures = list(filter(self.filter_lines, departures))

        try:
            val["attribution"] = self._sensordata["attribution"]
            val["departures"] = departures
            val["last_refresh"] = self._sensordata["last_updated"]
            val["next_departure_minutes"] = expected_minutes
            val["next_departure_time"] = expected_time
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val


class HASLRRArrivalSensor(HASLDevice):
    """HASL Arrival Sensor class."""

    def __init__(self, hass, config, siteid):
        """Initialize."""

        unit_table = {
            "min": "min",
            "time": "",
            "updated": "",
        }

        self._hass = hass
        self._config = config
        self._lines = config.data[CONF_LINES]
        self._siteid = str(siteid)
        self._name = f"RR Arrival Sensor {self._siteid} ({self._config.title})"
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._sensorproperty = config.data[CONF_SENSOR_PROPERTY]
        self._direction = config.data[CONF_DIRECTION]
        self._timewindow = config.data[CONF_TIMEWINDOW]
        self._nextarrival_minutes = "0"
        self._nextarrival_expected = "-"
        self._lastupdate = "-"
        self._unit_of_measure = unit_table.get(
            self._config.data[CONF_SENSOR_PROPERTY], "min"
        )
        self._sensordata = None
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

        if self._lines == "":
            self._lines = []
        if not isinstance(self._lines, list):
            self._lines = self._lines.split(",")

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")
        if self._worker.data.rrd[self._siteid]["api_lastrun"]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.rra[self._siteid]["api_lastrun"],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                    
                ):
                    try:
                        await self._worker.process_rra(self.hass)
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")
        self._sensordata = self._worker.data.rra[self._siteid]

        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return (
            f"rr-arrival-{self._siteid}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        sensorproperty = self._config.data[CONF_SENSOR_PROPERTY]

        if self._sensordata == []:
            return "Unknown"

        if sensorproperty == "min":
            next_arrival = self.nextArrival()
            if not next_arrival:
                return "-"

            adjustedDateTime = now()
            adjustedDateTime = adjustedDateTime.replace(tzinfo=None)
            delta = next_arrival["expected"] - adjustedDateTime
            expected_minutes = math.floor(delta.total_seconds() / 60)
            return expected_minutes

        # If the sensor should return the time at which next arrival occurs.
        if sensorproperty == "time":
            next_arrival = self.nextArrival()
            if not next_arrival:
                return "-"

            expected = next_arrival["expected"].strftime("%H:%M:%S")
            return expected

        if sensorproperty == "origin":
            next_arrival = self.nextArrival()
            if not next_arrival:
                return "-"

            origin = next_arrival["origin"]
            return origin

        if sensorproperty == "updated":
            return self._sensordata["last_updated"]

        # Fail-safe
        return "-"

    def nextArrival(self):
        if not self._sensordata:
            return None

        adjustedDateTime = now()
        adjustedDateTime = adjustedDateTime.replace(tzinfo=None)
        if "data" in self._sensordata:
            for arrival in self._sensordata["data"]:
                if arrival["expected"] > adjustedDateTime:
                    return arrival
        return None

    def filter_lines(self, arrival):
        if not self._lines or len(self._lines) == 0:
            return True
        return arrival["line"] in self._lines

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measure

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        if self._sensordata == [] or self._sensordata is None:
            return False
        else:
            return True

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes ."""

        # Initialize the state attributes.

        val = {}

        if self._sensordata == [] or self._sensordata is None:
            return val

        # Format the next expected time.
        next_arrival = self.nextArrival()
        if next_arrival:
            adjustedDateTime = now()
            adjustedDateTime = adjustedDateTime.replace(tzinfo=None)
            expected_time = next_arrival["expected"]
            delta = expected_time - adjustedDateTime
            expected_minutes = math.floor(delta.total_seconds() / 60)
            expected_time = expected_time.strftime("%H:%M:%S")
        else:
            expected_time = "-"
            expected_minutes = "-"

        # Set up the unit of measure.
        if self._unit_of_measure != "":
            val["unit_of_measurement"] = self._unit_of_measure

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Ok"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )

        if val["api_result"] != "Ok":
            return val

        arrivals = self._sensordata["data"]
        arrivals = list(filter(self.filter_lines, arrivals))

        try:
            val["attribution"] = self._sensordata["attribution"]
            val["arrivals"] = arrivals
            val["last_refresh"] = self._sensordata["last_updated"]
            val["next_arrival_minutes"] = expected_minutes
            val["next_arrival_time"] = expected_time
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val


class HASLDeviationSensor(HASLDevice):
    """HASL Deviation Sensor class."""

    def __init__(self, hass, config, deviationtype, deviationkey):
        """Initialize."""
        self._config = config
        self._hass = hass
        self._deviationkey = deviationkey
        self._deviationtype = deviationtype
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._name = f"SL {self._deviationtype.capitalize()} Deviation Sensor {self._deviationkey} ({self._config.title})"
        self._sensordata = []
        self._enabled_sensor
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")
        if self._worker.data.si2[f"{self._deviationtype}_{self._deviationkey}"][
            "api_lastrun"
        ]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.si2[
                            f"{self._deviationtype}_{self._deviationkey}"
                        ]["api_lastrun"],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                ):
                    try:
                        await self._worker.process_si2()
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")

        self._sensordata = self._worker.data.si2[
            f"{self._deviationtype}_{self._deviationkey}"
        ]
        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-deviation-{self._deviationtype}-{self._deviationkey}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return "Unknown"
        else:
            if "data" in self._sensordata:
                return len(self._sensordata["data"])
            else:
                return "Unknown"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        return self._sensordata != []

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes."""

        val = {}

        if self._sensordata == []:
            return val

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Ok"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )
        try:
            val["attribution"] = self._sensordata["attribution"]
            val["deviations"] = self._sensordata["data"]
            val["last_refresh"] = self._sensordata["last_updated"]
            val["deviation_count"] = len(self._sensordata["data"])
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val


class HASLVehicleLocationSensor(HASLDevice):
    """HASL Train Location Sensor class."""

    def __init__(self, hass, config, vehicletype):
        """Initialize."""
        self._hass = hass
        self._config = config
        self._vehicletype = vehicletype
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._name = f"SL {self._vehicletype} Location Sensor ({self._config.title})"
        self._sensordata = []
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")
        if self._worker.data.fp[self._vehicletype]["api_lastrun"]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.fp[self._vehicletype]["api_lastrun"],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                ):
                    try:
                        await self._worker.process_fp()
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")

        self._sensordata = self._worker.data.fp[self._vehicletype]
        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return (
            f"sl-fl-{self._vehicletype}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return "Unknown"
        else:
            if "data" in self._sensordata:
                return len(self._sensordata["data"])
            else:
                return "Unknown"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:train"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        return self._sensordata != []

    @property
    def extra_state_attributes(self):
        val = {}

        if self._sensordata == []:
            return val

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Success"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )
        try:
            val["attribution"] = self._sensordata["attribution"]
            val["data"] = self._sensordata["data"]
            val["last_refresh"] = self._sensordata["last_updated"]
            val["vehicle_count"] = len(self._sensordata["data"])
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val


class HASLTrafficStatusSensor(HASLDevice):
    """HASL Traffic Status Sensor class."""

    def __init__(self, hass, config, sensortype):
        """Initialize."""
        self._hass = hass
        self._config = config
        self._sensortype = sensortype
        self._enabled_sensor = config.data[CONF_SENSOR]
        self._name = (
            f"SL {self._sensortype.capitalize()} Status Sensor ({self._config.title})"
        )
        self._sensordata = []
        self._scan_interval = self._config.data[CONF_SCAN_INTERVAL] or 300
        self._worker = hass.data[DOMAIN]["worker"]

    async def async_update(self):
        """Update the sensor."""

        logger.debug("[async_update] Entered")
        logger.debug(f"[async_update] Processing {self._name}")
        if self._worker.data.tl2[self._config.data[CONF_TL2_KEY]]["api_lastrun"]:
            if self._worker.checksensorstate(self._enabled_sensor, STATE_ON):
                if (
                    self._sensordata == []
                    or self._worker.getminutesdiff(
                        now().strftime("%Y-%m-%d %H:%M:%S"),
                        self._worker.data.tl2[self._config.data[CONF_TL2_KEY]][
                            "api_lastrun"
                        ],
                    )
                    > self._config.data[CONF_SCAN_INTERVAL]
                ):
                    try:
                        await self._worker.process_tl2()
                        logger.debug("[async_update] Update processed")
                    except:
                        logger.debug("[async_update] Error occurred during update")
                else:
                    logger.debug("[async_update] Not due for update, skipping")

        self._sensordata = self._worker.data.tl2[self._config.data[CONF_TL2_KEY]]
        logger.debug("[async_update] Completed")
        return

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"sl-{self._sensortype}-sensor-{self._config.data[CONF_INTEGRATION_ID]}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._sensordata == []:
            return "Unknown"
        else:
            return self._sensordata["data"][self._sensortype]["status"]

    @property
    def icon(self):
        trafficTypeIcons = {
            "ferry": "mdi:ferry",
            "bus": "mdi:bus",
            "tram": "mdi:tram",
            "train": "mdi:train",
            "local": "mdi:train-variant",
            "metro": "mdi:subway-variant",
        }

        return trafficTypeIcons.get(self._sensortype)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ""

    @property
    def scan_interval(self):
        """Return the unique id."""
        return self._scan_interval

    @property
    def available(self):
        """Return true if value is valid."""
        if not self._sensordata or not "data" in self._sensordata:
            return False
        else:
            return True

    @property
    def extra_state_attributes(self):
        val = {}

        if self._sensordata == []:
            return val

        if self._sensordata["api_result"] == "Success":
            val["api_result"] = "Ok"
        else:
            val["api_result"] = self._sensordata["api_error"]

        # Set values of the sensor.
        val["scan_interval"] = self._scan_interval
        val["refresh_enabled"] = self._worker.checksensorstate(
            self._enabled_sensor, STATE_ON
        )

        try:
            val["attribution"] = self._sensordata["attribution"]
            val["status_icon"] = self._sensordata["data"][self._sensortype][
                "status_icon"
            ]
            val["events"] = self._sensordata["data"][self._sensortype]["events"]
            val["last_updated"] = self._sensordata["last_updated"]
        except:
            val["error"] = "NoDataYet"
            logger.debug(
                f"Data was not available for processing when getting attributes for sensor {self._name}"
            )

        return val
