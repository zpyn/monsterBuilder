""" This Module Creates a Maya creature rig"""
import re

import maya.cmds as cmds
import pymel.core as pm
import pymel.util

import MonsterUtils

class QuadGen():
    """
    """
    def __init__(self):
        # Get Tools
        self.controls = MonsterUtils.ControlGenerator()
    
    def create_spine_setup(self,creature_name,body_part,main_crv,joint_num, convert):
        # Create heiratchy
        self.main_grp = cmds.group(n=creature_name, w=1, em=1)
        self.joints_grp = cmds.group(n='joint_grp', p=self.main_grp, em=1)
        self.controls_grp = cmds.group(n='controls_grp', p=self.main_grp, em=1)
        self.bezier_grp = cmds.group(n='Bezier'+body_part+'_nodes', p=self.main_grp, em=1)
        self.crvs_grp= cmds.group(n='crvs_grp', p=self.bezier_grp, em=1)
        self.mtx_jnts_grp = cmds.group(n='mtx_jnts_grp', p=self.bezier_grp, em=1)
        self.clusters = cmds.group(n='clusters_grp', p=self.bezier_grp, em=1)
        self.clusters_up = cmds.group(n='clusters_up_grp', p=self.bezier_grp, em=1)

        # Validate and Convert Curve
        cmds.parent(main_crv,self.crvs_grp)
        if convert:
            main_crv = cmds.duplicate(main_crv, name='{}_base_cvr'.format(body_part))[0]
            cmds.hide(main_crv)
            cmds.select(main_crv)
            cmds.nurbsCurveToBezier()
            
        # Create Up Vector Curve
        up_crv = cmds.duplicate(main_crv, name='{}_upVector_cvr'.format(body_part))[0]
        cmds.hide(up_crv)
        # Translate
        cmds.setAttr("{0}.translateY".format(up_crv),10)

        # Create Joints
        mtx_jnts = self.create_bezier_chain(body_part, main_crv, up_crv, int(joint_num))
        fk_jnts =  self.create_chain_from_list(mtx_jnts, 'FK', body_part)
        ik_jnts = self.create_chain_from_list(mtx_jnts, 'IK', body_part)
        bind_jnts = self.create_chain_from_list(mtx_jnts, 'bnd', body_part)

        pm.hide(mtx_jnts)
        pm.hide(fk_jnts[0])
        pm.hide(ik_jnts[0])

        # Create blender control
        blend_ctrl_name = 'FKIK'+ body_part +'_M_ctrl'
        blend_ctrl_off = cmds.group(n=blend_ctrl_name+'_off', em=1, p= self.controls_grp)
        blend_ctrl = self.controls.create_cross(blend_ctrl_name)
        blend_ctrl_shape = cmds.listRelatives(blend_ctrl)[0]
        cmds.setAttr('{}.overrideEnabled'.format(blend_ctrl_shape), 1)
        cmds.setAttr('{}.overrideColor'.format(blend_ctrl_shape), 17)
        cmds.addAttr(blend_ctrl , niceName='FKIKBlend', longName='FKIKBlend', hidden= False, attributeType='double', k=1)
        cmds.parent(blend_ctrl,blend_ctrl_off)

        # Create FK setup
        fk_controls = self.create_fk_rig(fk_jnts, blend_ctrl)
        # Create IK setup
        ik_controls = self.crate_bezier_spine_setup(main_crv, up_crv,mtx_jnts)
        self.create_ik_rig(mtx_jnts,ik_jnts)
        # Create Ik/Fk blend
        self.create_IK_fk_blend(fk_jnts,ik_jnts,bind_jnts, blend_ctrl)

        # Add everything to Heriarchy
        cmds.parent( [x.name() for x in mtx_jnts ],self.mtx_jnts_grp)

        # Group Joints
        cmds.parent(fk_jnts[0].name(), self.joints_grp)
        cmds.parent(ik_jnts[0].name(), self.joints_grp)
        cmds.parent(bind_jnts[0].name(), self.joints_grp)

        cmds.parent( [x for x in fk_controls ],self.controls_grp)
        cmds.parent( [x for x in ik_controls ],self.controls_grp)

    def create_bezier_chain(self, name ,main_crv, up_crv, num_joints):
        """ 
        test
        """
        grain = 1.0 / (num_joints-1)
        ratios = [grain * x for x in range(num_joints)]
        total =[pymel.util.blend(0, 1, weight=ratio) for ratio in ratios]

        master_jnts = list()
        
        main_crv_shape = pm.listRelatives(main_crv,type= 'bezierCurve')[0]
        up_crv_shape = pm.listRelatives(up_crv,type= 'bezierCurve')[0]

        for n , val in enumerate(total):

            # Motion Path
            motion_path = pm.createNode("motionPath", n = "{0}_{1}_MPTH".format(name,n+1))
            motion_path.uValue.set(val)
            pm.connectAttr("{0}.worldSpace".format(main_crv_shape),"{0}.geometryPath".format(motion_path.name()))
            
            # World up vector
            nearestPoint = pm.createNode("nearestPointOnCurve", n = "{0}_{1}_NPOC".format(name,n+1))
            pm.connectAttr("{0}.worldSpace".format(up_crv_shape),"{0}.inputCurve".format(nearestPoint.name()))
            pm.connectAttr("{0}.allCoordinates".format(motion_path.name()),"{0}.inPosition".format(nearestPoint.name()))

            plusMinusAvarage = pm.createNode("plusMinusAverage", n = "{0}_{1}_RPMA".format(name,n+1))
            plusMinusAvarage.operation.set(2)
            pm.connectAttr("{0}.result.position".format(nearestPoint.name()),"{0}.input3D[0]".format(plusMinusAvarage.name()))
            pm.connectAttr("{0}.allCoordinates".format(motion_path.name()),"{0}.input3D[1]".format(plusMinusAvarage.name()))
            pm.connectAttr("{0}.output3D".format(plusMinusAvarage.name()),"{0}.worldUpVector".format(motion_path.name()))

            # Matrix Distribution
            fourByFourMatrix = pm.createNode("fourByFourMatrix", n = "{0}_{1}_FBFM".format(name,n+1))
            multMatrix = pm.createNode("multMatrix", n = "{0}_{1}_DMTM".format(name,n+1))
            pickMatrix = pm.createNode("pickMatrix", n = "{0}_{1}_PMTM".format(name,n+1))
            multMatrix_final = pm.createNode("multMatrix", n = "{0}_{1}_DMTM".format(name,n+1))
            joint_ = pm.createNode("joint", n = "{0}_{1}_jnt".format(name,str(n+1).zfill(3)))
            joint_.radius.set(2)

            master_jnts.append(joint_)

            pm.connectAttr("{0}.xCoordinate".format(motion_path.name()),"{0}.in30.".format(fourByFourMatrix.name()))
            pm.connectAttr("{0}.yCoordinate".format(motion_path.name()),"{0}.in31.".format(fourByFourMatrix.name()))
            pm.connectAttr("{0}.zCoordinate".format(motion_path.name()),"{0}.in32.".format(fourByFourMatrix.name()))
        
            pm.connectAttr("{0}.orientMatrix".format(motion_path.name()),"{0}.matrixIn[0]".format(multMatrix.name()))
            pm.connectAttr("{0}.output".format(fourByFourMatrix.name()),"{0}.matrixIn[1]".format(multMatrix.name()))
        
            # Connect pick Matrix
            pm.connectAttr("{0}.matrixSum".format(multMatrix.name()),"{0}.inputMatrix".format(pickMatrix.name()))
            pickMatrix.useTranslate.set(1)
            pickMatrix.useRotate.set(1)
            pickMatrix.useScale.set(0)
            pickMatrix.useShear.set(0)
        
            #Connect pick Matrix
            pm.connectAttr("{0}.outputMatrix".format(pickMatrix.name()),"{0}.matrixIn[0]".format(multMatrix_final.name()))
            
            #Connect pick Matrix
            pm.connectAttr("{0}.matrixSum".format(multMatrix_final.name()),"{0}.offsetParentMatrix".format(joint_.name()))
            
        return master_jnts
        
    def create_chain_from_list(self, reference_joints, name, type):
        """
        """
        cmds.select(cl=1)
        
        new_joints = list()
        for x in range(len(reference_joints)):
            cmds.select(cl=1)
            new_jnt= pm.joint(n = "{0}_{1}_{2}_jnt".format(type, name, str(x+1).zfill(3)))
            new_jnt.radius.set(.5)
            new_joints.append(new_jnt)
            point = pm.pointConstraint(reference_joints[x],new_jnt)
            pm.delete(point)

        pre_jnt = ''
        for jnt in reversed( new_joints):
            if pre_jnt != '':
                pm.parent(pre_jnt,jnt)
            pre_jnt = jnt
            
        
        # orient joints
        pm.joint(new_joints[0],orientJoint='xzy',secondaryAxisOrient='xup', ch=1, e=1)
    
        return new_joints
    
    def create_ik_rig(self, master_jnts, ik_jnts):

        for x in range(len(master_jnts)):
            cmds.parentConstraint(master_jnts[x].name(),ik_jnts[x].name())
        
    def crate_bezier_spine_setup(self,main_crv,up_crv, joints_ls):
        
        # Get Middle indexs
        total= int(len(joints_ls))
        middle= (total+1)/2

        if total % 2 != 0:
            middle_index = [middle-1]
        else:
            middle_index = [middle-1, middle]


        spine_clst_names = ['hip_clstr','hip_tangent_clstr','chest_tangent_clstr','chest_clstr']
        up_clst_names = ['hip_up_clst','middle_up_clst','null','chest_up_clst']
 
        main_crv_shape = pm.listRelatives(main_crv,type= 'bezierCurve')[0]
        up_crv_shape = pm.listRelatives(up_crv,type= 'bezierCurve')[0]

        # Create Clusters
        main_cls = self.create_cluster_all_cvs(main_crv_shape,spine_clst_names)
        up_vec_cls = self.create_cluster_for_up_vector(up_crv_shape,up_clst_names)

        # Create Cluster Setup
        hip_clstr_off = cmds.group(n= 'hip_clstr_off', em=1, w=1)
        pc = cmds.pointConstraint(joints_ls[0].name(),hip_clstr_off, mo=0)
        cmds.delete(pc)
        cmds.parent(main_cls[0], hip_clstr_off)
        cmds.parent(hip_clstr_off,self.clusters)
        cmds.hide(main_cls[0])

        chest_clstr_off = cmds.group(n= 'chest_clstr_off', em=1, w=1)
        pc = cmds.pointConstraint(joints_ls[-1].name(),chest_clstr_off, mo=0)
        cmds.delete(pc)
        cmds.parent(main_cls[-1], chest_clstr_off)
        cmds.parent(chest_clstr_off,self.clusters)
        cmds.hide(main_cls[-1])

        middle_clst_off = cmds.group(n= 'middle_clstr_off', em=1, w=1)
        pc = cmds.pointConstraint([joints_ls[x] for x in middle_index], middle_clst_off, mo=0)
        cmds.delete(pc)
        cmds.parent(middle_clst_off,self.clusters)

        hip_tangent_clstr_off = cmds.group(n= 'hip_tangent_clstr_off', em=1, p=middle_clst_off)
        pc = cmds.pointConstraint(joints_ls[0].name(),hip_tangent_clstr_off, mo=0)
        cmds.delete(pc)
        cmds.parent(main_cls[1], hip_tangent_clstr_off)
        cmds.hide(main_cls[1])

        chest_tangent_clstr= cmds.group(n= 'chest_tangent_clstr', em=1, p=middle_clst_off)
        pc = cmds.pointConstraint(joints_ls[-1].name(),chest_tangent_clstr, mo=0)
        cmds.delete(pc)
        cmds.parent(main_cls[2], chest_tangent_clstr)
        cmds.hide(main_cls[2])

        # Create Up Vector Setup
        hip_up_clst_off = cmds.group(n='hip_up_clst_off', w=1, em=1)
        pc = cmds.pointConstraint(up_vec_cls[0],hip_up_clst_off,mo=0)
        cmds.delete(pc)
        cmds.parent(up_vec_cls[0],hip_up_clst_off)
        cmds.hide(up_vec_cls[0])

        middle_up_clst_0ff = cmds.group(n='middle_up_clst_0ff', w=1, em=1)
        pc = cmds.pointConstraint(up_vec_cls[-1],middle_up_clst_0ff, mo=0)
        cmds.delete(pc)
        cmds.parent(up_vec_cls[-1],middle_up_clst_0ff)
        cmds.hide(up_vec_cls[-1])

        chest_up_clst_off = cmds.group(n='chest_up_clst_off', w=1, em=1)
        pc = cmds.pointConstraint(up_vec_cls[1],chest_up_clst_off, mo=0)
        cmds.delete(pc)
        cmds.parent(up_vec_cls[1],chest_up_clst_off)
        cmds.hide(up_vec_cls[1])

        cmds.parent(hip_up_clst_off,self.clusters_up)
        cmds.parent(middle_up_clst_0ff,self.clusters_up)
        cmds.parent(chest_up_clst_off,self.clusters_up)
       
        # Create Controls
        hip_ctrl= self.controls.create_sphere('hips_ctrl')
        hip_ctrl_shape = cmds.listRelatives(hip_ctrl)[0]
        cmds.setAttr('{}.overrideEnabled'.format(hip_ctrl_shape), 1)
        cmds.setAttr('{}.overrideColor'.format(hip_ctrl_shape), 17)

        hip_tangent_ctrl = self.controls.create_arrow('HipTangent_ctrl')
        hip_tangent_ctrl_shape = cmds.listRelatives(hip_tangent_ctrl)[0]
        cmds.setAttr('{}.overrideEnabled'.format(hip_tangent_ctrl_shape), 1)
        cmds.setAttr('{}.overrideColor'.format(hip_tangent_ctrl_shape), 22)

        middle_ctrl= self.controls.create_sphere('midSpine_ctrl')
        middle_ctrl_shape = cmds.listRelatives(middle_ctrl)[0]
        cmds.setAttr('{}.overrideEnabled'.format(middle_ctrl_shape), 1)
        cmds.setAttr('{}.overrideColor'.format(middle_ctrl_shape), 18)

        chest_ctrl = self.controls.create_sphere('chest_ctrl')
        chest_ctrl_shape = cmds.listRelatives(chest_ctrl)[0]
        cmds.setAttr('{}.overrideEnabled'.format(chest_ctrl_shape), 1)
        cmds.setAttr('{}.overrideColor'.format(chest_ctrl_shape), 17)

        chest_tangent_ctrl = self.controls.create_arrow('ChestTangent_ctrl')
        chest_tangent_ctrl_shape = cmds.listRelatives(chest_tangent_ctrl)[0]
        cmds.setAttr('{}.overrideEnabled'.format(chest_tangent_ctrl_shape), 1)
        cmds.setAttr('{}.overrideColor'.format(chest_tangent_ctrl_shape), 22)

        contols_ls = []
        hip_ctrl_off = cmds.group(n='hips_ctrl_off',em=1,w=1)
        contols_ls.append(hip_ctrl_off)
        cmds.parent(hip_ctrl,hip_ctrl_off)
        hip_tangent_ctrl_off = cmds.group(n='hip_tangent_ctrl_off',em=1,w=1)
        contols_ls.append(hip_tangent_ctrl_off)
        cmds.parent(hip_tangent_ctrl,hip_tangent_ctrl_off)
        middle_ctrl_off = cmds.group(n='middle_ctrl_off',em=1,w=1)
        contols_ls.append(middle_ctrl_off)
        cmds.parent(middle_ctrl,middle_ctrl_off)
        chest_ctrl_off = cmds.group(n='chest_ctrl_off',em=1,w=1)
        contols_ls.append(chest_ctrl_off)
        cmds.parent(chest_ctrl,chest_ctrl_off)
        chest_tangent_ctrl_off = cmds.group(n='chest_tangent_ctrl_off',em=1,w=1)
        contols_ls.append(chest_tangent_ctrl_off)
        cmds.parent(chest_tangent_ctrl,chest_tangent_ctrl_off)

        # Place Controls
        pc= cmds.pointConstraint(joints_ls[0].name(),hip_tangent_ctrl_off, mo=0)
        cmds.delete(pc)
        #cmds.setAttr('{0}.translateY'.format(hip_tangent_ctrl_off),3)
        #cmds.setAttr('{0}.rotateX'.format(hip_tangent_ctrl_off),180)
        #cmds.setAttr('{0}.rotateZ'.format(hip_tangent_ctrl_off),90)

        pc= cmds.pointConstraint(joints_ls[-1].name(),chest_tangent_ctrl_off, mo=0)
        cmds.delete(pc)
        #cmds.setAttr('{0}.translateY'.format(chest_tangent_ctrl_off),3)
        #cmds.setAttr('{0}.rotateZ'.format(chest_tangent_ctrl_off),-90)

        pc= cmds.pointConstraint(joints_ls[0].name(),hip_ctrl_off, mo=0)
        cmds.delete(pc)
        pc= cmds.pointConstraint([joints_ls[x].name() for x in middle_index],middle_ctrl_off, mo=0)
        cmds.delete(pc)
        pc= cmds.pointConstraint(joints_ls[-1].name(),chest_ctrl_off, mo=0)
        cmds.delete(pc)

        # Connect Controls
        cmds.parentConstraint(hip_ctrl,hip_clstr_off,mo=1)
        cmds.parentConstraint(middle_ctrl,middle_clst_off,mo=1)
        cmds.parentConstraint(chest_ctrl,chest_clstr_off,mo=1)

        # Connect Tangents
        cmds.connectAttr('{0}.rotate'.format(hip_tangent_ctrl),'{0}.rotate'.format(hip_tangent_clstr_off))
        cmds.connectAttr('{0}.rotate'.format(chest_tangent_ctrl),'{0}.rotate'.format(chest_tangent_clstr))
        
        cmds.parentConstraint(hip_tangent_ctrl,chest_tangent_ctrl,middle_ctrl_off,mo=1)

        # Connect Up Vectr
        cmds.parentConstraint(hip_ctrl,hip_up_clst_off,mo=1)
        cmds.parentConstraint(middle_ctrl,middle_up_clst_0ff,mo=1)
        cmds.parentConstraint(chest_ctrl,chest_up_clst_off,mo=1)

        cmds.parentConstraint(hip_ctrl,hip_tangent_ctrl_off,mo=1)
        cmds.parentConstraint(chest_ctrl,chest_tangent_ctrl_off,mo=1)

        return contols_ls

    def create_fk_rig(self, joints_ls, blend_ctrl):
        
        # Create Controls
        last_ctrl = ''
        empty = ''
        for jtn in joints_ls:
            jnt_number = jtn.name().split('_')[0][-1]
            ctr_grp_offst = pm.group(n= 'spine{0}_off'.format(jnt_number), em=1, w=1)
            if not empty:
                empty = ctr_grp_offst
            
            if jtn == joints_ls[-1]:
                normal = [0,0,1]
            else:
                 normal = [1,0,0]

            ctrl = pm.circle(n= 'spine{0}ctrl'.format(jnt_number),normal=normal, radius=8 )
            pm.parent(ctrl,ctr_grp_offst)
            
            # place joint
            pc = pm.pointConstraint(jtn,ctr_grp_offst)
            pm.delete(pc)
            oc = pm.orientConstraint(jtn,ctr_grp_offst)
            pm.delete(oc)
            
            # Main PC
            pc = pm.parentConstraint(ctrl,jtn)
            if last_ctrl:
                pm.parent(ctr_grp_offst,last_ctrl)
                
            last_ctrl= ctrl
            
            pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 0)
            pm.setAttr('{0}.visibility'.format(ctr_grp_offst.name()), 1)
            pm.setDrivenKeyframe('{0}.visibility'.format(ctr_grp_offst.name()), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))
            pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 10)
            pm.setAttr('{0}.visibility'.format(ctr_grp_offst.name()),0)
            pm.setDrivenKeyframe('{0}.visibility'.format(ctr_grp_offst.name()), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))
            
        return [empty]
        
    def create_IK_fk_blend(self, fk_joints, ik_joints, bind_joints, blend_ctrl):
    
        """
        """
        for i, val in enumerate(ik_joints):
            pc=pm.parentConstraint(fk_joints[i],ik_joints[i],bind_joints[i], mo=1)

            for attr in pm.listAttr(pc) :
                if re.match('[a-zA-Z0-9]+_[a-zA-Z]+_[0-9]+_[a-zA-Z]+W[0-9]', attr): 
                    if 'FK' in attr:
                        pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 0)
                        pm.setAttr('{0}.{1}'.format(pc.name(),attr), 1)
                        pm.setDrivenKeyframe('{0}.{1}'.format(pc.name(),attr), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))
                        pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 10)
                        pm.setAttr('{0}.{1}'.format(pc.name(),attr), 0)
                        pm.setDrivenKeyframe('{0}.{1}'.format(pc.name(),attr), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))
                    
                    if 'IK' in attr:
                        pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 0)
                        pm.setAttr('{0}.{1}'.format(pc.name(),attr), 0)
                        pm.setDrivenKeyframe('{0}.{1}'.format(pc.name(),attr), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))
                        pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 10)
                        pm.setAttr('{0}.{1}'.format(pc.name(),attr), 1)
                        pm.setDrivenKeyframe('{0}.{1}'.format(pc.name(),attr), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))

    def create_cluster_for_cv(self, curve, index, clstr_name):
        """ """
        cluster = cmds.cluster( "{0}.cv[{1}]".format(curve,index), name = clstr_name)
        return cluster

    def create_cluster_all_cvs(self, curve_node, clst_names_ls):
        """ """
        cluster_ls = list()
        for x in range(len(cmds.ls('{0}.cv[:]'.format(curve_node), fl = True))):
            clst = self.create_cluster_for_cv(curve_node,x, clst_names_ls[x])
            cluster_ls.append(clst)
        return cluster_ls
    
    def create_cluster_for_up_vector(self,curve_node, clst_names_ls):
        """ """
        cluster_ls = list()
        num_vertex = len(cmds.ls('{0}.cv[:]'.format(curve_node), fl = True))
        half = num_vertex/2
        middle_vxt = list()
        
        for x in range(num_vertex):
            if x > half or  x < half-1:
                clst =  self.create_cluster_for_cv(curve_node,x, clst_names_ls[x])
                cluster_ls.append(clst)
            else:
                middle_vxt.append(x)
                

        # Create middle cluster
        clst= cmds.cluster("{0}.cv[{1}:{2}]".format(curve_node,middle_vxt[0],middle_vxt[1],), name = clst_names_ls[1])
        cluster_ls.append(clst)
        return cluster_ls
    

    

        



