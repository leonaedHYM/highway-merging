from cistar.core.base_env import SumoEnvironment

from rllab.spaces import Box

import traci

import numpy as np
import pdb


class LoopEnvironment(SumoEnvironment):
    """
    Half-implementation for the environment for loop scenarios. Contains non-static methods pertaining to a loop
    environment (for example, headway calculation, leading-car, etc.)
    """

    def get_x_by_id(self, id):
        """
        Returns the position of the vehicle with specified id
        :param id: id of vehicle
        :return:
        """
        if self.vehicles[id]["edge"] == '':
            print("This vehicle teleported and its edge is now empty", id)
            return 0.
        return self.scenario.get_x(self.vehicles[id]["edge"], self.vehicles[id]["position"])

    def get_leading_car(self, veh_id, lane=None):
        """
        Returns the id of the car in-front of the specified car in the specified lane.
        :param veh_id: target car
        :param lane: target lane
        :return: id of leading car in target lane
        """
        target_pos = self.get_x_by_id(veh_id)

        front_dists = []
        for i in self.ids:
            if i != veh_id:
                c = self.vehicles[i]
                if lane is None or c['lane'] == lane:
                    dist_to = (self.get_x_by_id(i) - target_pos) % self.scenario.length
                    front_dists.append((c["id"], dist_to))

        if front_dists:
            return min(front_dists, key=(lambda x: x[1]))[0]
        else:
            return None

    def get_trailing_car(self, veh_id, lane=None):
        """
        Returns the id of the car behind the specified car in the specified lane.
        :param veh_id: target car
        :param lane: target lane
        :return: id of trailing car in target lane
        """
        target_pos = self.get_x_by_id(veh_id)

        backdists = []
        for i in self.ids:
            if i != veh_id:
                c = self.vehicles[i]
                if lane is None or c['lane'] == lane:
                    distto = (target_pos - self.get_x_by_id(i)) % self.scenario.length
                    backdists.append((c["id"], distto))

        if backdists:
            return min(backdists, key=(lambda x:x[1]))[0]
        else:
            return None

    def get_headway(self, veh_id, lane=None):
        # by default, will look in the same lane
        if lane is None:
            lane = self.vehicles[veh_id]["lane"]

        lead_id = self.get_leading_car(veh_id, lane)
        # if there's more than one car
        if lead_id:
            lead_pos = self.get_x_by_id(lead_id)
            lead_length = self.vehicles[lead_id]['length']
            this_pos = self.get_x_by_id(veh_id)
            return (lead_pos - lead_length - this_pos) % self.scenario.length
        # if there's only one car, return the loop length minus car length
        else: 
            return self.scenario.net_params["length"] - self.vehicles[veh_id]['length']

    def get_cars(self, veh_id, dxBack, dxForward, lane = None, dx = None):
        #TODO: correctly implement this method, and add documentation
        this_pos = self.get_x_by_id(veh_id)  # position of the car checking neighbors
        front_limit = this_pos + dxForward
        rear_limit = this_pos - dxBack

        if dx is None:
            dx = .5 * (dxBack + dxForward)

        cars = []
        for i in self.ids:
            if i != veh_id:
                car = self.vehicles[i]
                if lane is None or car['lane'] == lane:
                    # if a one-lane case or the correct lane
                    other_pos = self.get_x_by_id(i)
                    # if ((front_limit - other_pos) % self.scenario.length > 0) \
                    #     and ((other_pos - rear_limit) % self.scenario.length > 0):

                    # too lazy right now to differentiate between front/back distances
                    if (this_pos - other_pos) % self.scenario.length < dx:
                        cars.append(car['id'])

        return cars

    def get_distance_to_intersection(self, veh_id):
        """
        Determines the smallest distance from the current vehicle's position to any of the intersections.

        :param veh_id: vehicle identifier
        :return: a tuple containing the distance to the intersection and which side of the
                 intersection the vehicle will be arriving at.
        """
        this_pos = self.get_x_by_id(veh_id)

        if not self.scenario.intersection_edgestarts:
            raise ValueError("The scenario does not contain intersections.")

        dist = []
        intersection = []
        for intersection_tuple in self.scenario.intersection_edgestarts:
            dist.append((intersection_tuple[1] - this_pos) % self.scenario.length)
            intersection.append(intersection_tuple[0])

        ind = np.argmin(dist)

        return dist[ind], intersection[ind]
