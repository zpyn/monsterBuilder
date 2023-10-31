"""
"""
from functools import partial

from PySide2 import QtCore, QtWidgets, QtGui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import MonsterUtils as utils
reload(utils)
import monster_builder
reload(monster_builder)

class MonsterBuilderUI(MayaQWidgetDockableMixin,QtWidgets.QMainWindow):
    """
    This Class Contains the User Interfase for the Monster Builder Tool
    """
    def __init__(self, **kwargs):
        super(MonsterBuilderUI,self).__init__()
        self.set_ups = ['Spine', 'Neck', 'Tail']

        self.utils= utils.MonsterBuilderUtils()
        self.QuadBuilder = monster_builder.QuadGen()

        self.setup_ui(self)
        self.set_signal_connection()

    def setup_ui(self,window):
        self.setWindowTitle('Monster Builder')

        self.main_widget= QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_lyt = QtWidgets.QHBoxLayout()

        main_info_gbox = QtWidgets.QGroupBox("Main Info:")
        main_info_lyt = QtWidgets.QVBoxLayout()
        main_info_gbox .setLayout(main_info_lyt)

        self.name_le  = QtWidgets.QLabel('Character Name:')
        self.name_led = QtWidgets.QLineEdit()

        main_info_lyt.addWidget( self.name_le)
        main_info_lyt.addWidget( self.name_led)
        main_info_filler =QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        main_info_lyt.addItem(main_info_filler)

        rig_lyt = QtWidgets.QHBoxLayout()

        middle_setup_gbox = QtWidgets.QGroupBox("Middle Setup:")
        middle_rig_lyt = QtWidgets.QVBoxLayout()
        crv_in_lyt= QtWidgets.QHBoxLayout()
        middle_setup_gbox.setLayout(middle_rig_lyt)

        self.curve_le = QtWidgets.QLabel('Curve:')
        self.curve_led = QtWidgets.QLineEdit()
        self.curve_led.setObjectName('curve_led')
        self.curve_btn = QtWidgets.QPushButton('Load')
        self.curve_btn.setObjectName('curve_btn')
        
        self.curve_rb = QtWidgets.QRadioButton('Convert to Bezier')
        self.joints_le = QtWidgets.QLabel('Joints #:')
        self.joints_led = QtWidgets.QLineEdit()
        self.body_le = QtWidgets.QLabel('Body Part:')
        self.body_cbox = QtWidgets.QComboBox()
        self.body_cbox.addItems(self.set_ups)

        # Create Btns
        self.create_btn = QtWidgets.QPushButton('Create')
        self.create_btn.setObjectName('create_btn')
        
        crv_in_lyt.addWidget(self.curve_led)
        crv_in_lyt.addWidget(self.curve_btn)
        middle_rig_lyt.addWidget(self.curve_le)
        middle_rig_lyt.addLayout(crv_in_lyt)
        middle_rig_lyt.addWidget(self.curve_rb)
        middle_rig_lyt.addWidget(self.joints_le)
        middle_rig_lyt.addWidget(self.joints_led)
        middle_rig_lyt.addWidget(self.body_le)
        middle_rig_lyt.addWidget(self.body_cbox)
        middle_rig_lyt.addWidget(self.create_btn)
        rig_lyt.addLayout(middle_rig_lyt)
        filler_rig =QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        middle_rig_lyt.addItem(filler_rig)
        # Add group boxes to Main layout
        self.main_lyt.addWidget(main_info_gbox)
        self.main_lyt.addWidget(middle_setup_gbox)
        self.main_widget.setLayout(self.main_lyt)
        
    def set_signal_connection(self):
        #load
        field_name = self.curve_btn.objectName().replace('_btn', '_led')
        self.curve_btn.clicked.connect( partial(self.load_selected, field_name))
        #create
        self.create_btn.clicked.connect(self.create_rig)

    def load_selected(self, field_name):
         selected_node = self.utils.get_selected()
         eval("self.{0}.setText('{1}')".format(field_name, selected_node))

    def create_rig(self):
        # Collect Info
        creature_name = str(self.name_led.text())
        curve_name = str(self.curve_led.text())
        convert_to_bezier = self.curve_rb.isChecked() 
        joint_num = str(self.joints_led.text())
        body_part = str(self.body_cbox. currentText())

        # Create Rig
        self.QuadBuilder.create_spine_setup(creature_name,body_part,curve_name,joint_num,convert_to_bezier)
        print('Done!')


#mb = MonsterBuilderUI()
#mb.show(dockable=True, width=250, height=350)







    