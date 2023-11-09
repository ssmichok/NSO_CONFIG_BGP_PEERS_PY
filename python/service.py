# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service
import ncs.template
import sys


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')

        AsnList = []
        NeiList = []
        ArrayCount = 0
        DefaultInPolicy = "WSN_INET01_IN_POST"
        DefaultOutPolicy = "WSN_INET01_OUT_POST"
        Peers = service.Peer
        for Peer in Peers:
            Dev = Peer.device
	    Int = Peer.GigabitEthernet
            path = '/ncs:devices/device{"' + Dev + '"}'
            self.log.info('Device Path: ', path)
            with ncs.maapi.Maapi() as m:
                with ncs.maapi.Session(m, 'admin', 'python'):
                    with m.start_read_trans() as t:
                        with t.cursor(path + '/config/cisco-ios-xr:route-policy') as MyRoutePolicys:
                            flag = 0
                            for MyEachRoutePolicy in MyRoutePolicys:
                                MyPolicyName = MyEachRoutePolicy[0]
                                self.log.info('MyPolicyName: ', MyPolicyName)
                                if MyPolicyName == DefaultInPolicy:
                                    flag = flag + 1
                                if MyPolicyName == DefaultOutPolicy:
                                    flag = flag + 1
                            if flag != 2:
                                try:
                                    self.log.info('Input and/or Output Policies are not Configured on Device: ', Dev)
                                    raise NameError 
                                except NameError:
                                    ErrorString = "Input and/or Output Policies are not Configured on Device: " + Dev
                                    sys.exit(ErrorString)
                        if ArrayCount == 0:
                            with t.cursor(path + '/config/cisco-ios-xr:router/bgp/bgp-no-instance') as MyBgpAsns:
                                for MyBgpAsnIter in MyBgpAsns:
                                    self.log.info('MyBgpAsnIter.id: ', MyBgpAsnIter[0])
                                    AsnList.append(MyBgpAsnIter[0]) 
                            path1 = '/config/cisco-ios-xr:interface/GigabitEthernet{"' + Int + '"}'   
                            MyNeiIp = t.get_elem(path + path1 + '/ipv4/address/ip')
                            self.log.info('MyNeiIp: ', MyNeiIp)
                            NeiList.append(MyNeiIp)
                            ArrayCount = ArrayCount + 1
                        else:
                            with t.cursor(path + '/config/cisco-ios-xr:router/bgp/bgp-no-instance') as MyBgpAsns:
                                for MyBgpAsnIter in MyBgpAsns:
                                    self.log.info('MyBgpAsnIter.id: ', MyBgpAsnIter[0])
                                    AsnList.append(MyBgpAsnIter[0])
                            path1 = '/config/cisco-ios-xr:interface/GigabitEthernet{"' + Int + '"}'   
                            MyNeiIp = t.get_elem(path + path1 + '/ipv4/address/ip')
                            self.log.info('MyNeiIp: ', MyNeiIp)
                            NeiList.append(MyNeiIp)
        ArrayCount = 0
        for Peer in Peers:
            vars = ncs.template.Variables()
            vars.add('DEVICE', Peer.device)
            if ArrayCount == 0:
                vars.add('ASN', AsnList[0])
                vars.add('PEER_IP', NeiList[1])
                vars.add('PEER_ASN', AsnList[1])
                ArrayCount = ArrayCount + 1
            else:
                vars.add('ASN', AsnList[1])
                vars.add('PEER_IP', NeiList[0])
                vars.add('PEER_ASN', AsnList[0])
            vars.add('POLICY_IN', DefaultInPolicy)
            vars.add('POLICY_OUT', DefaultOutPolicy)
            template = ncs.template.Template(service)
            template.apply('service.template', vars)
            

    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    # @Service.pre_lock_create
    # def cb_pre_lock_create(self, tctx, root, service, proplist):
    #     self.log.info('Service plcreate(service=', service._path, ')')

    # @Service.pre_modification
    # def cb_pre_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class MyConfigureBgpPeers(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. Is is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('MyConfigureBgpPeers RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('service-servicepoint', ServiceCallbacks)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('MyConfigureBgpPeers FINISHED')
