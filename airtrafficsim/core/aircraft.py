import numpy as np

from airtrafficsim.core.traffic import Traffic
from airtrafficsim.core.navigation import Nav
from airtrafficsim.utils.unit_conversion import Unit
from airtrafficsim.utils.calculation import Cal
from airtrafficsim.utils.enums import APLateralMode, APThrottleMode


class Aircraft:
    """
    Aircraft class to represent the states of one individual aircraft, including get and set functions.
    """

    def __init__(self, traffic: Traffic, callsign, aircraft_type, flight_phase, configuration, lat, long, alt, heading, cas, fuel_weight, payload_weight, departure_airport="", departure_runway="", sid="", arrival_airport="", arrival_runway="", star="", approach="", flight_plan=[], flight_plan_index=0, cruise_alt=-1, initial_frequency=""):
        """
        Initialize one aircraft and add the aircraft to traffic array.

        Parameters
        ----------
        traffic : Traffic
            Points to the traffic array class. (The value must be self.traffic)
        callsign : str
            Call sign of the aircraft
        aircraft_type : str
            ICAO aircraft type
        flight_phase : FlightPhase.enums
            Initial flight phase
        configuration : Configuration.enums
            Initial configuration
        lat : float
            Initial latitude [deg]
        long : float
            Initial longitude [deg]
        alt : float
            Initial altitude [ft]
        heading : float
            Initial heading [deg]
        cas : float
            Initial CAS [kt]
        fuel_weight : float
            Initial fuel weight [kg]
        payload_weight : float
            Initial payload weight [kg]
        departure_airport : str, optional
            ICAO code of departure airport, by default ""
        departure_runway : str, optional
            Departure runway, by default ""
        sid : str, optional
            ICAO code of Standard Instrument Departure, by default ""
        arrival_airport : str, optional
            ICAO code of arrival airport, by default ""
        arrival_runway : str, optional
            Arrival runway, by default ""
        star : str, optional
            ICAO code Standard Terminal Arrival Procedure, by default ""
        approach : str, optional
            ILS approach procedure, by default ""
        flight_plan : list, optional
            Array of waypoints that the aircraft will fly, by default []
        cruise_alt : int, optional
            Target cruise altitude [ft], by default -1
        initial_frequency : string, optional
            Initial frequency of the aircraft, by default ""
        """
        self.traffic = traffic          # Pass traffic array reference
        self.index = self.traffic.add_aircraft(callsign, aircraft_type, flight_phase, configuration, lat, long, alt, heading, cas, fuel_weight, payload_weight,
                                               departure_airport, departure_runway, sid, arrival_airport, arrival_runway, star, approach, flight_plan, flight_plan_index,
                                               cruise_alt, initial_frequency)        # Add aircraft. Obtain aircraft index
        self.vectoring = ""

    def set_heading(self, heading):
        """
        Set the heading of the aircraft.

        Parameters
        ----------
        heading : float
            Heading [deg]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.ap.heading[index] = heading
        self.traffic.ap.lateral_mode[index] = APLateralMode.HEADING

    def set_speed(self, speed):
        """
        Set the speed of the aircraft.

        Parameters
        ----------
        speed : float
            Speed [kt]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.ap.cas[index] = speed
        self.traffic.ap.auto_throttle_mode[index] = APThrottleMode.SPEED

    # def set_mach(self, mach):
    #     """Set Mach [dimensionless]"""
    #     self.traffic.ap.mach[self.index] = mach

    def set_vs(self, vs):
        """
        Set vertical speed.

        Parameters
        ----------
        vs : float
            Vertical speed [ft/min]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.ap.vs[index] = vs

    def set_alt(self, alt):
        """
        Set altitude.

        Parameters
        ----------
        alt : float
            Altitude [ft]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        flight_plan_index = self.traffic.ap.flight_plan_index[index]
        self.traffic.ap.flight_plan_target_alt[index][flight_plan_index] = alt
        self.traffic.ap.alt[index] = alt

    def set_direct(self, waypoint):
        """
        Set direct to a waypoint.

        Parameters
        ----------
        waypoint : str
            ICAO code of the waypoint
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.ap.lateral_mode[index] = APLateralMode.LNAV

    def set_holding(self, holding_time, holding_fix, region):
        """
        Set holding procedure.

        Parameters
        ----------
        holding_time : float
            How long should the aircraft hold [second]
        holding_fix : float
            ICAO code of the fix that the aircraft should hold
        region : float
            ICAO code of the region that the aircraft should hold
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.ap.holding_round[index] = holding_time
        self.traffic.ap.holding_info[index] = Nav.get_holding_procedure(
            holding_fix, region)

    def set_vectoring(self, vectoring_time, v_2, fix):
        """
        Set vectoring procedure.

        Parameters
        ----------
        vectoring_time : float
            How long should the aircraft vector [second]
        v_2 : float
            The target speed speed [kt]
        fix : str
            ICAO code of the fix that the aircraft go next after vectoring
        """
        if not self.vectoring == fix and self.get_next_wp() == fix:
            self.vectoring = fix
            index = np.where(self.traffic.index == self.index)[0][0]

            new_dist = self.traffic.ap.dist[index] + Unit.kts2mps(
                self.traffic.cas[index] + v_2) * (vectoring_time) / 2000.0
            bearing = np.mod(self.traffic.ap.heading[index]+np.rad2deg(
                np.arccos(self.traffic.ap.dist[index]/new_dist)) + 360.0, 360.0)
            lat, long = Cal.cal_dest_given_dist_bearing(
                self.traffic.lat[index], self.traffic.long[index], bearing, new_dist / 2)

            # Add new virtual waypoint
            i = self.traffic.ap.flight_plan_index[index]
            self.traffic.ap.flight_plan_lat[index].insert(i, lat)
            self.traffic.ap.flight_plan_long[index].insert(i, long)
            self.traffic.ap.flight_plan_name[index].insert(i, "VECT")
            self.traffic.ap.flight_plan_target_alt[index].insert(
                i, self.traffic.ap.flight_plan_target_alt[index][i])
            self.traffic.ap.flight_plan_target_speed[index][i] = v_2
            self.traffic.ap.flight_plan_target_speed[index].insert(
                i, self.traffic.ap.flight_plan_target_speed[index][i])

    def set_altimeter(self, altimeter):
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.altimeter[index] = altimeter

    def set_flight_plan(self, arrival_airport=None, arrival_runway=None, star=None, approach=None, flight_plan=None, flight_plan_index=None, cruise_alt=None):
        """
        Set the flight plan of the aircraft.

        Parameters
        ----------
        flight_plan : String[]
            Flight plan of an aircraft
        """
        print(f"Set flight plan: {arrival_airport}, {arrival_runway}, {star}, {approach}, {flight_plan}, {cruise_alt}")

        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.ap.set_flight_plan(
            index,
            departure_airport=self.traffic.ap.departure_airport[index],
            departure_runway=self.traffic.ap.departure_runway[index],
            sid=self.traffic.ap.sid[index],
            arrival_airport=self.traffic.ap.arrival_airport[index] if arrival_airport is None else arrival_airport,
            arrival_runway=self.traffic.ap.arrival_runway[index] if arrival_runway is None else arrival_runway,
            star=self.traffic.ap.star[index] if star is None else star,
            approach=self.traffic.ap.approach[index] if approach is None else approach,
            flight_plan=self.traffic.ap.flight_plan_enroute[index] if flight_plan is None else flight_plan,
            flight_plan_index=self.traffic.ap.flight_plan_index[index] if flight_plan_index is None else flight_plan_index,
            cruise_alt=self.traffic.ap.cruise_alt[index] if cruise_alt is None else cruise_alt
        )

    def set_flight_phase(self, flight_phase):
        """
        Set flight phase.
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.flight_phase[index] = flight_phase

    def resume_own_navigation(self):
        """
        Resume own navigation to use autopilot instead of user commanded target.
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.ap.lateral_mode[index] = APLateralMode.LNAV
        self.traffic.ap.auto_throttle_mode[index] = APThrottleMode.AUTO

    def get_heading(self):
        """
        Get heading of aircraft.

        Returns
        -------
        Heading : float
            Heading [deg]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.heading[index]

    def get_cas(self):
        """
        Get Calibrated air speed of aircraft.

        Returns
        -------
        cas : float
            Calibrated air speed [knots]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.cas[index]

    def get_mach(self):
        """
        Get Mach number of aircraft.

        Returns
        -------
        mach : float
            Mach number [dimensionless]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.mach[index]

    def get_vs(self):
        """
        Get vertical speed of aircraft.

        Returns
        -------
        vs : float
            Vertical speed [ft/min]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.vs[index]

    def get_alt(self):
        """
        Get altitude of aircraft.

        Returns
        -------
        alt : float[]
            Altitude [ft]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.alt[index]

    def get_long(self):
        """
        Get longitude of aircraft.

        Returns
        -------
        long : float
            Longitude [deg]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.long[index]

    def get_lat(self):
        """
        Get latitude of aircraft.

        Returns
        -------
        lat : float
            Latitude [deg]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.lat[index]

    def get_fuel_consumed(self):
        """
        Get the total fuel consumed of aircraft.

        Returns
        -------
        fuel_consumed : float
            Fuel consumed [kg]
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.fuel_consumed[index]

    def get_next_wp(self):
        """
        Get next waypoint.

        Returns
        -------
        waypoint : str
            ICAO code of the next waypoing
        """
        index = np.where(self.traffic.index == self.index)[0][0]

        if self.traffic.ap.flight_plan_index[index] >= len(self.traffic.ap.flight_plan_name[index]):
            return None

        return self.traffic.ap.flight_plan_name[index][self.traffic.ap.flight_plan_index[index]]

    def get_wake(self):
        """
        Get wake category of aircraft.

        Returns
        -------
        Wake category : str
            The ICAO wake category of the aircraft.
        """
        index = np.where(self.traffic.index == self.index)[0][0]
        return self.traffic.perf.perf_model._Bada__wake_category[index]

    def set_frequency(self, frequency):
        index = np.where(self.traffic.index == self.index)[0][0]
        self.traffic.frequency[index] = frequency
