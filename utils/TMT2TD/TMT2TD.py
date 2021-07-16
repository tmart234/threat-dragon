## the script converts MS TMT models to Threat Dragon models
## goal: parse TMT XML model into a dict that can be dumped into THreat Dragon's json format
## Work in progress
## https://github.com/jgadsden/owasp-threat-dragon-models/tree/master/ThreatDragonModels

import xml.etree.ElementTree as ET
import os
import json
import tkinter as tk
from tkinter import filedialog

# namespace for prop elements
ele_namespace = {'b': 'http://schemas.datacontract.org/2004/07/ThreatModeling.KnowledgeBase'}
any_namespace = {'a': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays'}

def find_ele_type(tmt_type):
    tmt_type = tmt_type['{http://www.w3.org/2001/XMLSchema-instance}type']
    if tmt_type == "Connector" or tmt_type == "BorderBoundary":
        # flows have source and target, so choose different dict format
        cell = dict.fromkeys(['type', 'smooth','source','target','vertices','id', 'labels', 'z','hasOpenThreats','threats','attrs'])
        if tmt_type == "Connector":
            ele_type = "tm.Flow"
            cell['attrs'] = dict.fromkeys(['.marker-target', '.connection'])
            cell['attrs']['.marker-target'] = 'marker-target hasNoOpenThreats isInScope'
            cell['attrs']['.connection'] = 'connection hasNoOpenThreats isInScope'
        else:
            ele_type = "tm.Boundary"
            cell['attrs'] = dict()
        cell['smooth'] = True
    else:
        cell = dict.fromkeys(['type','size','pos','angle','id', 'z','hasOpenThreats','threats','attrs'])
        cell['size'] = dict.fromkeys(['width','height'])
        cell['pos'] = dict.fromkeys(['x','y'])
        cell['angle'] = int(0)
        cell['attrs'] = dict.fromkeys(['.element-shape','text','.element-text'])
        cell['attrs']['.element-shape'] = "element-shape hasNoOpenThreats isInScope"
        cell['attrs']['.element-text'] = "element-text hasNoOpenThreats isInScope"
        if tmt_type == "StencilRectangle":
            ele_type = "tm.Actor"
        elif tmt_type == "StencilEllipse":
            ele_type = "tm.Process"
        elif tmt_type == "StencilParallelLines":
            ele_type = "tm.Store"
        else:
            return None
    # TODO: change this
    cell['hasOpenThreats'] = False
    cell['threats'] = list()

    cell['type'] = ele_type
    return cell

def get_element(ele, _z):
        # GUID also at this level
    for ele4 in ele.findall('{http://schemas.microsoft.com/2003/10/Serialization/Arrays}Value'):
        # find element type and get cell dict format
        cell = find_ele_type(ele4.attrib)

        cell['z'] = _z
        # create a custom element properties dict
        ele_prop = dict.fromkeys(['PropName', 'PropGUID', 'PropValues', 'SelectedIndex'])
        ele_props = []
        # temp list of property values
        
        _values = []
        # get GUID
        for guid in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}Guid'):
            cell['id'] = guid.text
        # for gen_type in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}GenericTypeId'):
        #     element['GenericTypeId'] = gen_type.text
        for source in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}SourceGuid'):
            cell['source'] = source.text
        for target in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}TargetGuid'):
            cell['target'] = target.text
        # TODO: find size of the diagram from max dims in a seprate function
        # TODO: boundaries need to be converted from box to lines. Could present problems.
        for y in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}Height'):
            cell['pos']['y'] = int(y.text)
        for x in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}Left'):
            cell['pos']['x'] = int(x.text)
        for top in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}Top'):
            cell['size']['height'] = int(top.text)
        for width in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}Width'):
            cell['size']['width'] = int(width.text)

        for props in ele4.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model.Abstracts}Properties'):
            for types in props.findall('.//a:anyType', any_namespace):
            # get all child elements of anyType element, all properties located here
                for dis_name in types.findall('.//b:DisplayName', ele_namespace):   
                    ele_prop['PropName'] = dis_name.text
                for prop_guid in types.findall('.//b:Name', ele_namespace):   
                    if prop_guid.text:
                        ele_prop['PropGUID'] = prop_guid.text
                    else:
                        ele_prop['PropGUID'] = ''
                selection = types.find('.//b:SelectedIndex', ele_namespace)   
                if selection is None:
                    ele_prop['SelectedIndex'] = ''
                    # get all prop values
                    value = types.find('.//b:Value', ele_namespace)
                    # set values
                    if value.text is None:
                        _values.append('')
                    else:
                        _values.append(value.text)
                    # set custom element name 
                    if ele_prop['PropName'] == 'Name':
                        cell['attrs']['text'] = value.text
                        ele_prop['PropValues'] = _values.copy()
                else:
                    # get prop selection
                    ele_prop['SelectedIndex'] = selection.text
                    # get value list for selection
                    for values in types.findall('.//b:Value/*', ele_namespace):
                        _values.append(values.text)
                    ele_prop['PropValues'] = _values.copy()
                    # add prop to prop list
                _values.clear()
                ele_props.append(ele_prop.copy())
                ele_prop.clear()
        # save prop list to element dict
        # TODO: how do we transfer element properties to model? otherwise they will be left
        #element['properties'] = ele_props
        # print(element['properties'])
    return cell

def get_notes(_root):
        msgs = []
        for notes in _root.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Notes'):
            for note in notes.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Note'):
                for id in note.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Id'):
                    _id = id.text
                for message in note.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Message'):
                    _message = message.text
                msgs.append([_id,_message])
        return msgs

# get the summary info for the model
# missing: Assumptions, ExternalDependencies, 
def get_sum(_root):
    _sum = dict.fromkeys(['title','owner','description'])
    for sum in _root.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}MetaInformation'):
        for _title in sum.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}ThreatModelName'):
            title = _title.text
        for _owner in sum.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Owner'):
            owner = _owner.text
        for _desc in sum.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}HighLevelSystemDescription'):
            desc = _desc.text
    _sum['title'] = title
    _sum['owner'] = owner
    _sum['description'] = desc
    return _sum

# get the contributors as a list
def get_contribs(_root):
    for sum in _root.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}MetaInformation'):
        for _contribs in sum.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Contributors'):
            contribs = _contribs.text.split(',')
    contrib_list = []
    c_dict = dict.fromkeys(['name'])
    for p in contribs:
        c_dict['name'] = p
        contrib_list.append(c_dict)
    return contrib_list

# get the contributors as a list
# should work like contributors but doesn't
def get_reviewers(_root):
    for sum in _root.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}MetaInformation'):
        for _reviewrs in sum.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Reviewer'):
            reviewers = _reviewrs.text
    return reviewers

def main():
    root = tk.Tk()
    root.withdraw()

    try:
        file_path = filedialog.askopenfilename(parent=root, filetypes=[("MS threat model files", "*.tm7")])
    except FileNotFoundError:
        print('Must choose file path, quitting... ')
        quit()
    if not file_path:
        print('Must choose file path, quitting... ')
        quit()

    root.destroy()
    tree = ET.parse(file_path)
    root = tree.getroot()

    # get file name
    base_name = os.path.splitext(file_path)[0]
    file_path = base_name + '.json'

    model = dict.fromkeys(['summary','detail'])
    summary = get_sum(root)
    model['summary'] = summary
    model['detail'] = dict.fromkeys(['contributors','diagrams','reviewer'])
    model['detail']['contributors'] = get_contribs(root)
    model['detail']['reviewer'] = get_reviewers(root)

    # find all note elements
    notes = get_notes(root)

    diagrams = list()
    model['detail']['diagrams'] = diagrams
    # add diagrams
    with open(file_path, 'w') as outfile:
        # get elements, borders, and notes
        for child in root.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}DrawingSurfaceList'):
            diagram_num = 0
            # indexing/numbering for TD elements
            z = 1
            # what is diagramType?
            model['detail']['diagrams'].append(dict.fromkeys(['title','thumbnail','id', 'diagramJson', 'diagramType']))
            # cells contain all stencils and flows
            model['detail']['diagrams'][diagram_num]['thumbnail'] = None
            model['detail']['diagrams'][diagram_num]['diagramJson'] = dict.fromkeys(['cells'])
            model['detail']['diagrams'][diagram_num]['diagramJson']['cells'] = list()
            for ele in child.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}DrawingSurfaceModel'):
                for header in ele.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Header'):
                    diagram = header.text
                    model['detail']['diagrams'][diagram_num]['title'] = diagram
                for ele2 in ele.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Borders'):
                    # this level enumerates a model's elements
                    for borders in ele2.findall('{http://schemas.microsoft.com/2003/10/Serialization/Arrays}KeyValueOfguidanyType'):
                        stencil = get_element(borders, z)
                        model['detail']['diagrams'][diagram_num]['diagramJson']['cells'].append(stencil)
                        z=z+1
                for ele2 in ele.findall('{http://schemas.datacontract.org/2004/07/ThreatModeling.Model}Lines'):
                    # this level enumerates a model's elements
                    for lines in ele2.findall('{http://schemas.microsoft.com/2003/10/Serialization/Arrays}KeyValueOfguidanyType'):
                    # Flows. Unlike stencils, flows have a source and target guids
                        line = get_element(lines, z)
                        model['detail']['diagrams'][diagram_num]['diagramJson']['cells'].append(line)
                        z=z+1
                # diagram id
                model['detail']['diagrams'][diagram_num]['id'] = diagram_num
                diagram_num = diagram_num + 1
        # Serializing json
        json.dump(model, outfile, indent=4, sort_keys=False)


if __name__ == '__main__':
   main()

