from datetime import datetime
from pathlib import Path
import numpy as np

from core.environment import Environment
from core.aircraft import Aircraft
from utils.enums import Configuration, Flight_phase

class FullFlightDemo(Environment):

    def __init__(self):
        # Initialize environment super class
        super().__init__(file_name = Path(__file__).name.removesuffix('.py'), #File name (do not change)
                        number_of_traffic = 1,
                        start_time = datetime.fromisoformat('2022-03-22T00:00:00'),
                        end_time = 5500,
                        era5_weather = False,
                        bada_perf = True 
                        )

        # Add aircraft
        self.aircraft_full = Aircraft(self.traffic, call_sign="FULL", aircraft_type="A320", flight_phase=Flight_phase.TAKEOFF, configuration=Configuration.TAKEOFF,
                                                    lat=22.307500, long=113.932833, alt=0.0, heading=254.0, cas=149.0, fuel_weight=5273.0, payload_weight=12000.0,
                                                    cruise_alt=37000,
                                                    departure_runway=[], arrival_runway=["RCTP/05R", 25.061500, 121.224167, 108],
                                                    flight_plan=["PRAWN", "RUMSY", "TUNNA", "TROUT", "OCEAN", "RASSE", "CONGA", "ENVAR", "DADON", "EXTRA", "RENOT", "TONGA", "BOCCA", "ELBER", "BRAVO", "JAMMY"],
                                                    target_speed=[   205,     230,    310,      310,    0.78,    0.78,    0.78,    0.78,    0.78,    0.78,    0.78,    0.78,    0.78,     300,     200,     200],
                                                    target_alt=[   37000,   37000,  37000,    37000,   37000,   37000,   37000,   37000,   37000,   37000,   37000,   37000,   37000,    37000,   1000,    1000])
                                                    # target_alt=[    5000,   14000,  37000,    37000,   37000,   37000,   37000,   37000,   37000,   37000,   37000,   37000,   29000,    4000,    4000,    4000])
                                                    # VHHH/25L OCEAN2B OCEAN V3 ENVAR M750 TONGA TONGA1A RCTP/05R
                                                    # departure_runway=[22.182675,113.555815], "HOKOU", "TULIP" approach
                                                    # TODO: 0 cas

    def should_end(self):
        if (self.global_time > 60 and  np.all((self.traffic.alt == 0))):
            return True
        else:
            return False
        

    def atc_command(self):
        # User algorithm
        print("Set ATC command")
        