# Copyright 2012 Red Hat, Inc.
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

import time

from eventlet import greenthread
from mox3 import mox
from oslotest import base as test_base

from oslo_service import loopingcall


class LoopingCallTestCase(test_base.BaseTestCase):

    def setUp(self):
        super(LoopingCallTestCase, self).setUp()
        self.num_runs = 0

    def test_return_true(self):
        def _raise_it():
            raise loopingcall.LoopingCallDone(True)

        timer = loopingcall.FixedIntervalLoopingCall(_raise_it)
        self.assertTrue(timer.start(interval=0.5).wait())

    def test_return_false(self):
        def _raise_it():
            raise loopingcall.LoopingCallDone(False)

        timer = loopingcall.FixedIntervalLoopingCall(_raise_it)
        self.assertFalse(timer.start(interval=0.5).wait())

    def _wait_for_zero(self):
        """Called at an interval until num_runs == 0."""
        if self.num_runs == 0:
            raise loopingcall.LoopingCallDone(False)
        else:
            self.num_runs = self.num_runs - 1

    def test_repeat(self):
        self.num_runs = 2

        timer = loopingcall.FixedIntervalLoopingCall(self._wait_for_zero)
        self.assertFalse(timer.start(interval=0.5).wait())

    def test_interval_adjustment(self):
        """Ensure the interval is adjusted to account for task duration."""
        self.num_runs = 3

        now = time.time()
        second = 1
        smidgen = 0.01

        m = mox.Mox()
        m.StubOutWithMock(greenthread, 'sleep')
        greenthread.sleep(mox.IsAlmost(0.02))
        greenthread.sleep(mox.IsAlmost(0.0))
        greenthread.sleep(mox.IsAlmost(0.0))
        m.StubOutWithMock(loopingcall, '_ts')
        loopingcall._ts().AndReturn(now)
        loopingcall._ts().AndReturn(now + second - smidgen)
        loopingcall._ts().AndReturn(now)
        loopingcall._ts().AndReturn(now + second + second)
        loopingcall._ts().AndReturn(now)
        loopingcall._ts().AndReturn(now + second + smidgen)
        loopingcall._ts().AndReturn(now)
        m.ReplayAll()

        timer = loopingcall.FixedIntervalLoopingCall(self._wait_for_zero)
        timer.start(interval=1.01).wait()
        m.UnsetStubs()
        m.VerifyAll()
