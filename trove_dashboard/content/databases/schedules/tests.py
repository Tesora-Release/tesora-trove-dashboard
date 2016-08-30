# Copyright 2016 Tesora Inc.
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

import six

from django.core.urlresolvers import reverse
from django import http

from mistralclient.api import client as mistral_client

from mox3 import mox
from mox3.mox import IsA  # noqa

from troveclient import common

from trove_dashboard import api
from trove_dashboard.test import helpers as test


DETAILS_URL = reverse('horizon:project:databases:schedules:schedule_detail',
                      args=('id', 'id',))
EXECUTIONS_URL = reverse('horizon:project:databases:schedules:view_executions',
                         args=('id', 'id',))
SCHEDULES_URL = reverse('horizon:project:databases:schedules:view_schedules',
                        args=['id'])


class ScheduleTests(test.TestCase):
    def stub_mistralclient(self, expected_calls=1):
        if not hasattr(self, "mistralclient"):
            self.mox.StubOutWithMock(mistral_client, 'client')
            self.mistralclient = self.mox.CreateMock(mistral_client.client)
            while expected_calls:
                (mistral_client.client(username=mox.IgnoreArg(),
                                       auth_token=mox.IgnoreArg(),
                                       project_id=mox.IgnoreArg(),
                                       auth_url=mox.IgnoreArg(),
                                       service_type="workflowv2",
                                       cacert=None,
                                       insecure=False)
                 .AndReturn(self.mistralclient))
                expected_calls -= 1
        return self.mistralclient

    @test.create_stubs({
        api.trove: ('instance_get', 'schedule_list',)
    })
    def test_index(self):
        instance = self.databases.first()
        schedules = common.Paginated(self.database_backup_schedules.list())
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(instance))
        (api.trove.schedule_list(IsA(http.HttpRequest),
                                 instance.id,
                                 self.stub_mistralclient())
            .AndReturn(schedules))
        self.mox.ReplayAll()
        res = self.client.get(SCHEDULES_URL)
        self.assertTemplateUsed(res,
                                'project/databases/schedules/schedules.html')

    @test.create_stubs({
        api.trove: ('instance_get', 'schedule_list',)
    })
    def test_index_exception(self):
        instance = self.databases.first()
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(instance))
        (api.trove.schedule_list(IsA(http.HttpRequest),
                                 instance.id,
                                 self.stub_mistralclient())
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()
        res = self.client.get(SCHEDULES_URL)
        self.assertTemplateUsed(res,
                                'project/databases/schedules/schedules.html')
        self.assertMessageCount(res, error=1)

    @test.create_stubs({
        api.trove: ('instance_get', 'schedule_list',)
    })
    def test_index_instance_get_exception(self):
        instance = self.databases.first()
        schedules = common.Paginated(self.database_backup_schedules.list())
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndRaise(self.exceptions.trove))
        (api.trove.schedule_list(IsA(http.HttpRequest),
                                 instance.id,
                                 self.stub_mistralclient())
            .AndReturn(schedules))
        self.mox.ReplayAll()
        res = self.client.get(SCHEDULES_URL)
        self.assertTemplateUsed(res,
                                'project/databases/schedules/schedules.html')
        self.assertMessageCount(res, error=2)

    @test.create_stubs({
        api.trove: ('schedule_show',)
    })
    def test_details(self):
        (api.trove.schedule_show(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 self.stub_mistralclient())
            .AndReturn(self.database_backup_schedules.first()))
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'project/databases/schedules/'
                                     'detail.html')
        self.assertContains(res, "description of backup1")

    @test.create_stubs({
        api.trove: ('schedule_show',)
    })
    def test_details_with_no_parent_id(self):
        (api.trove.schedule_show(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 self.stub_mistralclient())
            .AndReturn(self.database_backup_schedules.list()[1]))
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'project/databases/schedules/'
                                     'detail.html')
        self.assertContains(res, "description of backup2")

    @test.create_stubs({
        api.trove: ('schedule_show',)
    })
    def test_details_exception(self):
        (api.trove.schedule_show(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 self.stub_mistralclient())
            .AndRaise(self.exceptions.trove))
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertRedirectsNoFollow(res, SCHEDULES_URL)

    @test.create_stubs({
        api.trove: ('schedule_delete', 'schedule_list',)
    })
    def test_schedule_delete(self):
        schedules = common.Paginated(self.database_backup_schedules.list())
        (api.trove.schedule_list(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 self.stub_mistralclient())
            .AndReturn(schedules))
        (api.trove.schedule_delete(IsA(http.HttpRequest),
                                   schedules[0].id,
                                   self.stub_mistralclient())
            .AndReturn(None))
        self.mox.ReplayAll()
        action_string = u"schedules__delete__%s" % schedules[0].id
        form_data = {'action': action_string}
        res = self.client.post(SCHEDULES_URL, form_data)
        self.assertRedirectsNoFollow(res, SCHEDULES_URL)

    @test.create_stubs({
        api.trove: ('schedule_create',)
    })
    def test_create_new_schedule(self):
        new_schedule = {
            "name": "backup1",
            "pattern": "* * 0 * *",
            "description": "This is the backup1 schedule",
        }

        (api.trove.schedule_create(IsA(http.HttpRequest),
                                   IsA(six.text_type),
                                   IsA(six.text_type),
                                   IsA(six.text_type),
                                   description=IsA(six.text_type),
                                   mistral_client=self.stub_mistralclient())
            .AndReturn(new_schedule))

        self.mox.ReplayAll()

        url = reverse('horizon:project:databases:schedules:create_schedule',
                      args=['id'])
        post = {
            'method': 'CreateScheduleForm',
            'instance_id': 'id',
            'name': 'backup1',
            'pattern': '* * 0 * *',
            'description': 'This is the backup1 schedule'
        }

        res = self.client.post(url, post)
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)

    @test.create_stubs({
        api.trove: ('execution_list', 'instance_get', 'schedule_show',)
    })
    def test_executions(self):
        instance = self.databases.first()
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(instance))
        (api.trove.execution_list(IsA(http.HttpRequest),
                                  IsA(six.text_type),
                                  self.stub_mistralclient(),
                                  marker=None)
            .AndReturn((self.database_backup_schedule_executions.list(),
                        False)))
        (api.trove.schedule_show(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 self.stub_mistralclient())
            .AndReturn(self.database_backup_schedules.first()))
        self.mox.ReplayAll()
        res = self.client.get(EXECUTIONS_URL)
        self.assertTemplateUsed(res,
                                'project/databases/schedules/executions.html')

    @test.create_stubs({
        api.trove: ('execution_list', 'instance_get', 'schedule_show',)
    })
    def test_executions_exception(self):
        instance = self.databases.first()
        (api.trove.instance_get(IsA(http.HttpRequest), IsA(six.text_type))
            .AndReturn(instance))
        (api.trove.execution_list(IsA(http.HttpRequest),
                                  IsA(six.text_type),
                                  self.stub_mistralclient(),
                                  marker=None)
            .AndRaise(self.exceptions.trove))
        (api.trove.schedule_show(IsA(http.HttpRequest),
                                 IsA(six.text_type),
                                 self.stub_mistralclient())
            .AndReturn(self.database_backup_schedules.first()))
        self.mox.ReplayAll()
        res = self.client.get(EXECUTIONS_URL)
        self.assertTemplateUsed(res,
                                'project/databases/schedules/executions.html')

    @test.create_stubs({
        api.trove: ('execution_delete', 'execution_list',)
    })
    def test_execution_delete(self):
        executions = self.database_backup_schedule_executions.list()
        (api.trove.execution_list(IsA(http.HttpRequest),
                                  IsA(six.text_type),
                                  self.stub_mistralclient(),
                                  marker=None)
            .AndReturn((executions, False)))
        (api.trove.execution_delete(IsA(http.HttpRequest),
                                    executions[0].id,
                                    self.stub_mistralclient())
            .AndReturn(None))
        self.mox.ReplayAll()
        action_string = u"executions__delete__%s" % executions[0].id
        form_data = {'action': action_string}
        res = self.client.post(EXECUTIONS_URL, form_data)
        self.assertRedirectsNoFollow(res, EXECUTIONS_URL)
