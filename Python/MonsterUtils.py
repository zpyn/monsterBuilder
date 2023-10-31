"""This Module contains all the small task that are used to build a rig in Autodesk Maya"""

import maya.cmds as cmds
import pymel.core as pm

class MonsterBuilderUtils():
    """
    """
    def __init__(self):
        pass

    def get_selected(self):
        selected_node = cmds.ls(selection=1)[0]
        return selected_node

    def create_chain_from_list(self, reference_joints, name, type):
        """
        Creates a joint chain based in a list of given joints

        Args:
            reference_joints (ls):  A list of pymel joint nodes
            name (str): The name of the body part this chain will drive
            type (str): the type of rig (IK/Fk) this chain will become

        Returns:
            list(nodes): A list with the new joint nodes
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
    
    def create_fk_rig(self, joints_ls, blend_ctrl= None):
        
        # Create Controls
        last_ctrl = ''
        for jtn in joints_ls:
            jnt_number = jtn.name().split('_')[0][-1]
            ctr_grp_offst = pm.group(n= 'spine{0}_off'.format(jnt_number), em=1, w=1)
            
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
            
            if blend_ctrl:
                pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 0)
                pm.setAttr('{0}.visibility'.format(ctr_grp_offst.name()), 1)
                pm.setDrivenKeyframe('{0}.visibility'.format(ctr_grp_offst.name()), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))
                pm.setAttr('{0}.{1}'.format(blend_ctrl,'FKIKBlend'), 10)
                pm.setAttr('{0}.visibility'.format(ctr_grp_offst.name()),0)
                pm.setDrivenKeyframe('{0}.visibility'.format(ctr_grp_offst.name()), cd='{0}.{1}'.format(blend_ctrl,'FKIKBlend'))
                
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



class ControlGenerator():
    """
    """

    def __init__(self):
        pass

    def create_sphere(self,name):
        """
        """
        points = [(0,0,1),(0,0.5,0.866025),(0,0.866025,0.5),(0,1,0),(0,0.866025,-0.5),(0,0.5,-0.866025),(0,0,-1),(0,-0.5,-0.866025),(0, -0.866025,-0.5 ),(0,-1,0),(0,-0.866025,0.5),(0,-0.5,0.866025),
           (0,0,1),(0.707107,0,0.707107),(1,0,0),(0.707107,0,-0.707107),(0,0,-1),(-0.707107,0,-0.707107),(-1,0,0),(-0.866025,0.5,0),(-0.5,0.866025,0),(0,1,0),(0.5,0.866025,0),( 0.866025,0.5,0),
           (1,0,0),(0.866025,-0.5,0),(0.5,-0.866025,0),(0,-1,0),(-0.5,-0.866025,0),(-0.866025,-0.5,0),(-1,0,0),(-0.707107,0,0.707107),(0,0,1)]
        knots=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32]
        curve = cmds.curve(n=name,d=1, p= points, k=knots)
        return curve

    def create_arrow(self,name):
        """
        """
        points=[(0,0,-0.99),(-0.66,0,0),(-0.33,0,0),(-0.33,0,0.66),(0.33,0,0.66),(0.33,0,0),(0.66,0,0),(0,0,-0.99)]
        knots = [0,1,2,3,4,5,6,7]
        curve = cmds.curve(n=name,d=1, p= points, k=knots)
        return curve

    def create_cross(self, name):
        """
        """
        points=[(0.4,0,-0.4),(0.4,0,-2),(-0.4,0,-2),(-0.4,0,-0.4),(-2,0,-0.4),(-2,0,0.4),(-0.4,0,0.4),
                (-0.4,0,2),(0.4,0,2),(0.4,0,0.4),(2,0,0.4),(2,0,-0.4),(0.4, 0, -0.4)]
        knots=[0,1,2,3,4,5,6,7,8,9,10,11,12]
        curve = cmds.curve(n=name,d=1, p= points, k=knots)
        return curve
