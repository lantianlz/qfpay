# -*- coding: utf-8 -*-
import sys
import os

# 引入父目录来引入其他模块
SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([os.path.abspath(os.path.join(SITE_ROOT, '../')),
                 os.path.abspath(os.path.join(SITE_ROOT, '../../')),
                 os.path.abspath(os.path.join(SITE_ROOT, '../../../')),
                 ])
os.environ['DJANGO_SETTINGS_MODULE'] = 'www.settings'

import datetime
from django.test import TestCase
from common import utils
from django.utils.encoding import smart_str


from www.account import interface


class SimpleTest(TestCase):

    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
        self.assertTrue(True)
        self.assertFalse(False)

    def runTest(self):
        pass

    def test_regist(self):
        ub = interface.UserBase()
        # print ub.set_password(raw_password='123')
        # print ub.check_password(raw_password='123')
        errcode, result = ub.regist_user_with_transaction(email='lz@3-10.cc', nick='orange', password='851129',
                                                          re_password="851129", ip='127.0.0.1', mobilenumber='13005012270')
        if not errcode == 0:
            print result.__repr__()
            print result.encode('utf-8')
        else:
            print result
        return 'ok'

    def re_test(self):
        from www.account.models import Profile
        from cPickle import dumps, loads
        p = Profile.objects.all()[0]

        user = interface.UserBase().get_user_by_email('lantian-lz@163.com')
        print user.is_authenticated
        print type(user.is_authenticated)
        print user.is_staff
        print user.is_staff()
        print dumps(user)

    def test_qr_code(self):
        qrb = interface.InviteQrcodeBase()
        uib = interface.UserInviteBase()
        vib = interface.VerifyInfoBase()
        # print qrb.create_channel_qrcode(name="PC首页渠道码")
        # print qrb.create_user_qrcode(user_id="2fda4e0053da11e6bd8ad0a637ea4c03")
        print uib.create_ui(unique_code="invite_5", to_user_id="1dd8cd8c561711e693c7d0a637ea4c03")
        # print vib.add_verfy_info(user_id="2fda4e0053da11e6bd8ad0a637ea4c03", name="11", mobile="22",
        #                          title="33", company_name="44")


if __name__ == '__main__':
    st = SimpleTest()
    # print st.test_basic_addition()
    # print utils.uuid_without_dash()
    # print st.test_regist()
    # st.re_test()

    st.test_qr_code()
