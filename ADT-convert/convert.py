import hl7
import json

from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier
from fhir.resources.encounter import Encounter, EncounterLocation
from fhir.resources.location import Location
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.bundle import Bundle, BundleEntry

test_msg_1 = "MSH|^~\&|ADT1|GOOD HEALTH HOSPITAL|GHH LAB, INC.|GOOD HEALTH HOSPITAL|198808181126|SECURITY|ADT^A01^ADT_A01|MSG00001|P|2.8||\rEVN|A01|200708181123||\rPID|1||PATID1234^5^M11^ADT1^MR^GOOD HEALTH HOSPITAL~123456789^^^USSSA^SS||EVERYMAN^ADAM^A^III||19610615|M||C|2222 HOME STREET^^GREENSBORO^NC^27401-1020|GL|(555) 555-2004|(555)555-2004||S||PATID12345001^2^M10^ADT1^AN^A|444333333|987654^NC|\rNK1|1|NUCLEAR^NELDA^W|SPO^SPOUSE||||NK^NEXT OF KIN\rPV1|1|I|2000^2012^01||||004777^ATTEND^AARON^A|||SUR||||ADM|A0|"
test_msg_2 = "MSH|^~\&|SIMHOSP|SFAC|RAPP|RFAC|20200508130643||ADT^A01|5|T|2.3|||AL||44|ASCII\rEVN|A01|20200508130643|||C006^Wolf^Kathy^^^Dr^^^DRNBR^PRSNL^^^ORGDR|\rPID|1|2590157853^^^SIMULATOR MRN^MRN|2590157853^^^SIMULATOR MRN^MRN~2478684691^^^NHSNBR^NHSNMBR||Esterkin^AKI Scenario 6^^^Miss^^CURRENT||19890118000000|F|||170 Juice Place^^London^^RW21 6KC^GBR^HOME||020 5368 1665^HOME|||||||||R^Other - Chinese^^^||||||||\rPD1|||FAMILY PRACTICE^^12345|\rPV1|1|I|RenalWard^MainRoom^Bed 1^Simulated Hospital^^BED^Main"

def get_or_none(msg, seg, seg_inst, field, repet, component=None):
    try:
        if component is not None:
            toRet = str(msg[seg][seg_inst][field][repet][component])
        else:
            toRet = str(msg[seg][seg_inst][field][repet])
    except IndexError:
        return None
    else:
        if toRet == "":
            return None
        else:
            return toRet

def append_non_null(lst, val):
    if val is not None:
        lst.append(val)
    else:
        pass

def map_encounter_class(v2code):
    map_dict = {
        "E": Coding(code="EMER", display="emergency", system="http://terminology.hl7.org/CodeSystem/v3-ActCode"),
        "I": Coding(code="IMP", display="inpatient encounter", system="http://terminology.hl7.org/CodeSystem/v3-ActCode"),
        "O": Coding(code="AMB", display="ambulatory", system="http://terminology.hl7.org/CodeSystem/v3-ActCode"),
        "P": Coding(code="PRENC", display="pre-admission", system="http://terminology.hl7.org/CodeSystem/v3-ActCode"),
        "R": Coding(code="R", display="Recurring patient", system="http://terminology.hl7.org/CodeSystem/v2-0004"),
        "B": Coding(code="B", display="Obstetrics", system="http://terminology.hl7.org/CodeSystem/v2-0004"),
        "C": Coding(code="C", display="Commercial Account", system="http://terminology.hl7.org/CodeSystem/v2-0004"),
        "N": Coding(code="N", display="Not Applicable", system="http://terminology.hl7.org/CodeSystem/v2-0004"),
        "U": Coding(code="U", display="Unknown", system="http://terminology.hl7.org/CodeSystem/v2-0004")
    }
    return map_dict[v2code]

def map_encounter_type(v2code):
    map_dict = {
        "A": Coding(code="A",display="Accident", system="http://terminology.hl7.org/CodeSystem/v2-0007"),
        "E": Coding(code="E",display="Emergency", system="http://terminology.hl7.org/CodeSystem/v2-0007"),
        "L": Coding(code="L",display="Labor and Delivery", system="http://terminology.hl7.org/CodeSystem/v2-0007"),
        "R": Coding(code="R",display="Routine",system="http://terminology.hl7.org/CodeSystem/v2-0007"),
        "N": Coding(code="N",display="Newborn (Birth in healthcare facility)", system="http://terminology.hl7.org/CodeSystem/v2-0007"),
        "U": Coding(code="U",display="Urgent", system="http://terminology.hl7.org/CodeSystem/v2-0007"),
        "C": Coding(code="E",display="Elective", system="http://terminology.hl7.org/CodeSystem/v2-0007")
    }
    return map_dict[v2code]

def get_encounter_status(v2obj):
    map_dict = {
        "E": Coding(code="in-progress", display="In Progress", system="http://hl7.org/fhir/encounter-status"),
        "I": Coding(code="in-progress", display="In Progress", system="http://hl7.org/fhir/encounter-status"),
        "O": Coding(code="in-progress", display="In Progress", system="http://hl7.org/fhir/encounter-status"),
        "P": Coding(code="planned", display="Planned", system="http://hl7.org/fhir/encounter-status"),
        "R": Coding(code="in-progress", display="In Progress", system="http://hl7.org/fhir/encounter-status"),
        "B": Coding(code="in-progress", display="In Progress", system="http://hl7.org/fhir/encounter-status"),
        "C": Coding(code="in-progress", display="In Progress", system="http://hl7.org/fhir/encounter-status"),
        "N": Coding(code="in-progress", display="In Progress", system="http://hl7.org/fhir/encounter-status"),
        "U": Coding(code="unknown", display="Unknown", system="http://hl7.org/fhir/encounter-status")
    }
    try_class = get_or_none(v2obj, "PV1", 0, 2, 0, 0)
    try_disch = get_or_none(v2obj, "PV1", 0, 45, 0, 0)
    if try_disch is not None:
        return Coding(code="finished", display="Finished", system="http://hl7.org/fhir/encounter-status")
    elif try_class is not None:
        return map_dict[try_class]
    else:
        return map_dict["U"]

def convert_v2_date(v2DTM:str):
    return v2DTM[0:4] + "-" + v2DTM[4:6] + "-" + v2DTM[6:8]

def v2toFHIR(v2str):
    msg = v2str.replace("\n", "")
    msg = hl7.parse(msg)
    fhir_pat = Patient()
    fhir_id = Identifier()
    fhir_name = HumanName()

    cc_unknown = CodeableConcept()
    cc_unknown.text = "U"
    coding_unknown = map_encounter_class("U")

    fhir_encounter = Encounter(status="unknown", type=[], class_fhir=coding_unknown)
    fhir_encounter_loc = Location()

    # SEGEMENT: PID
    # ID
    fhir_pat.id = get_or_none(msg, "PID", 0, 1, 0, 0)

    # NAME
    fhir_name.family = get_or_none(msg, "PID", 0, 5, 0, 0)
    fhir_name.given = []
    append_non_null(fhir_name.given, get_or_none(msg, "PID", 0, 5, 0, 1))
    append_non_null(fhir_name.given, get_or_none(msg, "PID", 0, 5, 0, 2))

    fhir_name.prefix = []
    append_non_null(fhir_name.prefix, get_or_none(msg, "PID", 0, 5, 0, 4))

    fhir_name.suffix = []
    append_non_null(fhir_name.suffix, get_or_none(msg, "PID", 0, 5, 0, 3))
    append_non_null(fhir_name.suffix, get_or_none(msg, "PID", 0, 5, 0, 5))

    # IDENTIFIER
    fhir_id.value = get_or_none(msg, "PID", 0, 3, 1, 0)

    fhir_pat.name = [fhir_name]
    fhir_pat.identifier = [fhir_id]

    # DATE OF BIRHT
    
    fhir_pat_dob = get_or_none(msg, "PID", 0, 7, 0)
    if fhir_pat_dob is not None:
        fhir_pat.birthDate = str(convert_v2_date(fhir_pat_dob))

    #fhir_pat.birthDate

    #print(fhir_pat.birthDate)

    fhir_ref_pat = Reference(reference="Patient/"+str(fhir_pat.id))

    # SEGMENT: PV1
    fhir_encounter.subject = fhir_ref_pat
    fhir_encounter.id = get_or_none(msg, "PV1", 0, 1, 0, 0)

    try_class = get_or_none(msg, "PV1", 0, 2, 0, 0)
    if try_class is not None:
        fhir_encounter.class_fhir = map_encounter_class(try_class)

    enc_status = get_encounter_status(msg)
    fhir_encounter.status = enc_status.code

    try_type = get_or_none(msg, "PV1", 0, 4, 0, 0)
    if try_type is not None:
        enc_type = map_encounter_type(try_type)
        fhir_encounter.type = [CodeableConcept(text=enc_type.code, coding=enc_type)]

    fhir_encounter_loc = Location()
    fhir_encounter_loc.identifier = []
    append_non_null(fhir_encounter_loc.identifier, get_or_none(msg, "PV1", 0, 3, 0, 0))
    append_non_null(fhir_encounter_loc.identifier, get_or_none(msg, "PV1", 0, 3, 0, 1))
    append_non_null(fhir_encounter_loc.identifier, get_or_none(msg, "PV1", 0, 3, 0, 2))
    append_non_null(fhir_encounter_loc.identifier, get_or_none(msg, "PV1", 0, 3, 0, 3))
    append_non_null(fhir_encounter_loc.identifier, get_or_none(msg, "PV1", 0, 3, 0, 6))
    append_non_null(fhir_encounter_loc.identifier, get_or_none(msg, "PV1", 0, 3, 0, 7))

    fhir_encounter_loc.id = "1"
    fhir_ref_loc = Reference(reference="Location/1")

    #fhir_encounter.location = [EncounterLocation(location=fhir_ref_loc)]

    # BUNDLE
    fhir_bundle = Bundle(type="collection")
    fhir_bundle.entry = []

    fhir_bundle.entry.append(BundleEntry(resource=fhir_pat))
    fhir_bundle.entry.append(BundleEntry(resource=fhir_encounter))
    #fhir_bundle.entry.append(BundleEntry(resource=fhir_encounter_loc))
    
    return fhir_bundle.json()

def print_info(fhir_msg):
    bund = Bundle.parse_obj(json.loads(fhir_msg))
    pat : Patient = bund.entry[0].resource
    pat_fname = ' '.join(pat.name[0].given) 
    pat_lname = pat.name[0].family
    pat_dob = pat.birthDate
    print(f"{pat_lname}, {pat_fname} (DOB: {pat_dob})")

#fhir_conv = v2toFHIR(test_msg_2)
#print(fhir_conv)

#print_info(fhir_conv)