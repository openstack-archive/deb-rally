# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from rally.plugins.openstack import scenario
from rally.task import atomic
from rally.task import utils as bench_utils


class CeilometerScenario(scenario.OpenStackScenario):
    """Base class for Ceilometer scenarios with basic atomic actions."""

    RESOURCE_NAME_PREFIX = "rally_ceilometer_"

    def _get_alarm_dict(self, **kwargs):
        """Prepare and return an alarm dict for creating an alarm.

        :param kwargs: optional parameters to create alarm
        :returns: alarm dictionary used to create an alarm
        """
        alarm_id = self._generate_random_name()
        alarm = {"alarm_id": alarm_id,
                 "name": alarm_id,
                 "description": "Test Alarm"}

        alarm.update(kwargs)
        return alarm

    @atomic.action_timer("ceilometer.list_alarms")
    def _list_alarms(self, alarm_id=None):
        """List alarms.

        List alarm matching alarm_id. It fetches all alarms
        if alarm_id is None.

        :param alarm_id: specifies id of the alarm
        :returns: list of alarms
        """
        if alarm_id:
            return self.clients("ceilometer").alarms.get(alarm_id)
        else:
            return self.clients("ceilometer").alarms.list()

    @atomic.action_timer("ceilometer.create_alarm")
    def _create_alarm(self, meter_name, threshold, kwargs):
        """Create an alarm.

        :param meter_name: specifies meter name of the alarm
        :param threshold: specifies alarm threshold
        :param kwargs: contains optional features of alarm to be created
        :returns: alarm
        """
        alarm_dict = self._get_alarm_dict(**kwargs)
        alarm_dict.update({"meter_name": meter_name,
                           "threshold": threshold})
        alarm = self.clients("ceilometer").alarms.create(**alarm_dict)
        return alarm

    @atomic.action_timer("ceilometer.delete_alarm")
    def _delete_alarm(self, alarm_id):
        """Delete an alarm.

        :param alarm_id: specifies id of the alarm
        """
        self.clients("ceilometer").alarms.delete(alarm_id)

    @atomic.action_timer("ceilometer.update_alarm")
    def _update_alarm(self, alarm_id, alarm_dict_delta):
        """Update an alarm.

        :param alarm_id: specifies id of the alarm
        :param alarm_dict_delta: features of alarm to be updated
        """
        self.clients("ceilometer").alarms.update(alarm_id, **alarm_dict_delta)

    @atomic.action_timer("ceilometer.get_alarm_history")
    def _get_alarm_history(self, alarm_id):
        """Assemble the alarm history requested.

        :param alarm_id: specifies id of the alarm
        :returns: list of alarm changes
        """
        return self.clients("ceilometer").alarms.get_history(alarm_id)

    @atomic.action_timer("ceilometer.get_alarm_state")
    def _get_alarm_state(self, alarm_id):
        """Get the state of the alarm.

        :param alarm_id: specifies id of the alarm
        :returns: state of the alarm
        """
        return self.clients("ceilometer").alarms.get_state(alarm_id)

    @atomic.action_timer("ceilometer.set_alarm_state")
    def _set_alarm_state(self, alarm, state, timeout):
        """Set the state of the alarm.

        :param alarm: alarm instance
        :param state: an alarm state to be set
        :param timeout: The number of seconds for which to attempt a
                         successful check of the alarm state.
        :returns: alarm in the set state
        """
        self.clients("ceilometer").alarms.set_state(alarm.alarm_id, state)
        return bench_utils.wait_for(alarm,
                                    is_ready=bench_utils.resource_is(state),
                                    update_resource=bench_utils
                                    .get_from_manager(),
                                    timeout=timeout, check_interval=1)

    @atomic.action_timer("ceilometer.list_events")
    def _list_events(self):
        """Get list of user's events.

        It fetches all events.
        :returns: list of events
        """
        return self.admin_clients("ceilometer").events.list()

    @atomic.action_timer("ceilometer.get_event")
    def _get_event(self, event_id):
        """Get event with specific id.

        Get event matching event_id.

        :param event_id: specifies id of the event
        :returns: event
        """
        return self.admin_clients("ceilometer").events.get(event_id)

    @atomic.action_timer("ceilometer.list_event_types")
    def _list_event_types(self):
        """Get list of all event types.

        :returns: list of event types
        """
        return self.admin_clients("ceilometer").event_types.list()

    @atomic.action_timer("ceilometer.list_event_traits")
    def _list_event_traits(self, event_type, trait_name):
        """Get list of event traits.

        :param event_type: specifies the type of event
        :param trait_name: specifies trait name
        :returns: list of event traits
        """
        return self.admin_clients("ceilometer").traits.list(event_type,
                                                            trait_name)

    @atomic.action_timer("ceilometer.list_event_trait_descriptions")
    def _list_event_trait_descriptions(self, event_type):
        """Get list of event trait descriptions.

        :param event_type: specifies the type of event
        :returns: list of event trait descriptions
        """
        return self.admin_clients("ceilometer").trait_descriptions.list(
            event_type)

    @atomic.action_timer("ceilometer.list_meters")
    def _list_meters(self):
        """Get list of user's meters."""
        return self.clients("ceilometer").meters.list()

    @atomic.action_timer("ceilometer.list_resources")
    def _list_resources(self):
        """List all resources.

        :returns: list of all resources
        """
        return self.clients("ceilometer").resources.list()

    @atomic.action_timer("ceilometer.list_samples")
    def _list_samples(self):
        """List all Samples.

        :returns: list of all samples
        """
        return self.clients("ceilometer").samples.list()

    @atomic.action_timer("ceilometer.get_resource")
    def _get_resource(self, resource_id):
        """Retrieve details about one resource."""
        return self.clients("ceilometer").resources.get(resource_id)

    @atomic.action_timer("ceilometer.get_stats")
    def _get_stats(self, meter_name):
        """Get stats for a specific meter.

        :param meter_name: Name of ceilometer meter
        """
        return self.clients("ceilometer").statistics.list(meter_name)

    @atomic.action_timer("ceilometer.create_meter")
    def _create_meter(self, **kwargs):
        """Create a new meter.

        :param name_length: Length of meter name to be generated
        :param kwargs: Contains the optional attributes for meter creation
        :returns: Newly created meter
        """
        name = self._generate_random_name()
        samples = self.clients("ceilometer").samples.create(
            counter_name=name, **kwargs)
        return samples[0]

    @atomic.action_timer("ceilometer.query_alarms")
    def _query_alarms(self, filter, orderby, limit):
        """Query alarms with specific parameters.

        If no input params are provided, it returns all the results
        in the database.

        :param limit: optional param for maximum number of results returned
        :param orderby: optional param for specifying ordering of results
        :param filter: optional filter query
        :returns: queried alarms
        """
        return self.clients("ceilometer").query_alarms.query(
            filter, orderby, limit)

    @atomic.action_timer("ceilometer.query_alarm_history")
    def _query_alarm_history(self, filter, orderby, limit):
        """Query history of an alarm.

        If no input params are provided, it returns all the results
        in the database.

        :param limit: optional param for maximum number of results returned
        :param orderby: optional param for specifying ordering of results
        :param filter: optional filter query
        :returns: alarm history
        """
        return self.clients("ceilometer").query_alarm_history.query(
            filter, orderby, limit)

    @atomic.action_timer("ceilometer.create_sample")
    def _create_sample(self, counter_name, counter_type, counter_unit,
                       counter_volume, resource_id=None, **kwargs):
        """Create a Sample with specified parameters.

        :param counter_name: specifies name of the counter
        :param counter_type: specifies type of the counter
        :param counter_unit: specifies unit of the counter
        :param counter_volume: specifies volume of the counter
        :param resource_id: specifies resource id for the sample created
        :param kwargs: contains optional parameters for creating a sample
        :returns: created sample
        """
        kwargs.update({"counter_name": counter_name,
                       "counter_type": counter_type,
                       "counter_unit": counter_unit,
                       "counter_volume": counter_volume,
                       "resource_id": resource_id if resource_id
                       else self._generate_random_name(
                           prefix="rally_resource_")})
        return self.clients("ceilometer").samples.create(**kwargs)

    @atomic.action_timer("ceilometer.query_samples")
    def _query_samples(self, filter, orderby, limit):
        """Query samples with specified parameters.

        If no input params are provided, it returns all the results
        in the database.

        :param limit: optional param for maximum number of results returned
        :param orderby: optional param for specifying ordering of results
        :param filter: optional filter query
        :returns: queried samples
        """
        return self.clients("ceilometer").query_samples.query(
            filter, orderby, limit)
