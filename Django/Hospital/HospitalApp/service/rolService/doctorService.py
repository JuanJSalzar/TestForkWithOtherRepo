import datetime
from HospitalApp import models
from Hospital.conection_mongo import collection
from django.core.exceptions import ObjectDoesNotExist
from HospitalApp.service import instances

# ------------------------------------- OTHERS

def itemNumber(orderinstance):
    return orderinstance.orderMedication_Order.count() + orderinstance.orderProcedure_Order.count() + 1

def getMedicationData(medication):
    return {
        "id": str(medication.id),
        "dose": medication.dose,
        "duration": medication.duration,
        "amount": medication.amount,
        "item": medication.item
    }

def getProcedureData(procedure):
    return {
        "id": str(procedure.id),
        "amount": procedure.amount,
        "frequency": procedure.frequency,
        "item": procedure.item,
        "specialAssistance": procedure.specialAssistance,
    }

def getDiagnosticAidData(diagnosticAid):
    return {
        "id": str(diagnosticAid.id),
        "quantity": diagnosticAid.quantity,
        "specialAssistance": diagnosticAid.specialAssistance,
        "idSpecialist": str(diagnosticAid.idSpecialist.cedula) if diagnosticAid.idSpecialist else None
    }

def getOrderData(order):
    orderData = {
        "id": str(order.id),
        "patientId": str(order.patientId.id),
        "doctorId": str(order.doctorId.cedula),
        "orderMedications": [getMedicationData(medication) for medication in order.orderMedication_Order.all()],
        "orderProcedures": [getProcedureData(procedure) for procedure in order.orderProcedure_Order.all()],
        "orderDiagnosticAids": [getDiagnosticAidData(diagnosticAid) for diagnosticAid in order.orderDiagnositcAid_Order.all()]
    }
    orderData = {key: value for key, value in orderData.items() if value}
    return orderData

# ------------------------------------- MEDICAL RECORDS
# --------- GET

def getOrdersData(patientId):
    orders = models.Order.objects.filter(patientId=patientId)
    return {str(order.id): getOrderData(order) for order in orders}

def processHistoryData(historyData, ordersData):
    for historyEntry in historyData:
        orderId = historyEntry.pop("orderId", None)
        historyEntry["order"] = ordersData.get(orderId, {})

def getMedicalRecords(patientId):
    try:
        patientIdStr = str(patientId)
        clinicalHistory = collection.find_one({"_id": patientIdStr})

        if clinicalHistory:
            ordersData = getOrdersData(patientId)
            for historyData in clinicalHistory.get("historias", {}).values():
                processHistoryData(historyData, ordersData)

            return clinicalHistory
        else:
            raise Exception("No se encontraron historias clínicas para el paciente")

    except ObjectDoesNotExist:
        raise Exception("El paciente no existe")

    except Exception as e:
        raise Exception("Ha ocurrido un error: " + str(e))


# --------- POST
def createMedicalRecord(patientId, idDoctor, consultationReason, symptoms, diagnosis):
    patient = models.Patient.objects.get(id=patientId)
    patientIdStr = str(patient.id)
    medicalRecord = collection.find_one({"_id": patientIdStr})
    if medicalRecord is None:
        raise Exception("El paciente no tiene historial clínico")

    date = datetime.date.today().strftime("%d/%m/%Y")
    newClinicalHistory = {}
    newClinicalHistory["idDoctor"] = idDoctor
    newClinicalHistory["consultationReason"] = consultationReason
    newClinicalHistory["symptoms"] = symptoms
    newClinicalHistory["diagnosis"] = diagnosis

    if date in medicalRecord["historias"]:
        medicalRecord["historias"][date].append(newClinicalHistory)
    else:
        medicalRecord["historias"][date] = [newClinicalHistory]

    collection.update_one({"_id": patientIdStr}, {"$set": medicalRecord})

# ------------------------------------- ORDERS
# --------- POST

def generateOrder(patientId, doctorId):
    try:
        idPatientInstance = instances.patientInstance(patientId)
        idDoctorInstance = instances.personInstance(doctorId)
        order = models.Order(patientId=idPatientInstance, doctorId=idDoctorInstance)
        order.save()
        
        medicalRecord = getMedicalRecords(patientId)

        date = datetime.date.today().strftime("%d/%m/%Y")

        if date in medicalRecord["historias"]:
            for history in medicalRecord["historias"][date]:
                history["orderId"] = str(order.id)
        else:
            medicalRecord["historias"][date] = [{"orderId": str(order.id)}]

        collection.update_one({"_id": str(patientId)}, {"$set": medicalRecord})

    except models.Order.DoesNotExist:
        raise Exception("No se pudo crear la orden para el paciente")

    except Exception as e:
        raise Exception("Ha ocurrido un error: " + str(e))


def generateOrderDiagnosticAid(orderId, diagnosticAidId, quantity, specialAssistance, idSpecialist):
    if models.OrderMedication.objects.filter(idOrder=orderId).exists():
        raise Exception("No se puede agregar una orden de ayuda diagnóstica a una orden que contiene medicamentos")
    if models.OrderProcedure.objects.filter(idOrder=orderId).exists():
        raise Exception("No se puede agregar una orden de ayuda diagnóstica a una orden que contiene procedimientos")
    
    if not models.Order.objects.filter(id=orderId).exists():
        raise Exception("La orden no existe")
    
    idOrderInstance = instances.orderInstance(orderId)
    idDiagnosticAidInstance = instances.diagnosticAidInstance(diagnosticAidId)
    
    if specialAssistance:
        if idSpecialist is None or not models.Person.objects.filter(cedula=idSpecialist).exists():
            raise Exception("Especialista no válido o no encontrado")
        idSpecialistAidInstance = instances.personInstance(idSpecialist)
    else:
        idSpecialistAidInstance = None
    
    orderDiagnosticAid = models.OrderDiagnosticAid(
        idOrder=idOrderInstance,
        DiagnosticAid=idDiagnosticAidInstance,
        quantity=quantity,
        specialAssistance=specialAssistance,
        idSpecialist=idSpecialistAidInstance
    )
    orderDiagnosticAid.save()


def generateOrderMedication(idOrder, idMedication, dose, duration, amount):
    if models.OrderDiagnosticAid.objects.filter(idOrder=idOrder).exists():
        raise Exception("No se puede agregar una orden de medicamentos a una orden que contiene ayuda diagnóstica")
    if models.Order.objects.filter(id=idOrder).exists() and models.Medication.objects.filter(id=idMedication).exists():
        idOrderInstance = instances.orderInstance(idOrder)
        idMedicationInstance = instances.medicationInstance(idMedication)
        numItem = itemNumber(idOrderInstance)
        orderMedication = models.OrderMedication(idOrder=idOrderInstance, idMedication=idMedicationInstance, dose=dose, duration=duration, amount=amount, item=numItem)
        orderMedication.save()
    else:
        raise Exception("La orden o la medicación no existen")


def generateOrderProcedure(idOrder, idProcedure, amount, frequency, specialAssistance, idSpecialist):
    if models.OrderDiagnosticAid.objects.filter(idOrder=idOrder).exists():
        raise Exception("No se puede agregar una orden de procedimientos a una orden que contiene ayuda diagnóstica")
    if models.Order.objects.filter(id=idOrder).exists() and models.Procedure.objects.filter(id=idProcedure).exists():
        idProcedureInstance = instances.procedureInstance(idProcedure)
        idOrderInstance = instances.orderInstance(idOrder)
        numItem = itemNumber(idOrderInstance)
        if specialAssistance:
            if models.Person.objects.filter(cedula=idSpecialist).exists():
                idSpecialistInstance = instances.personInstance(idSpecialist)
                orderProcedure = models.OrderProcedure(idOrder=idOrderInstance, idProcedure=idProcedureInstance, amount=amount, frequency=frequency, item=numItem, specialAssistance=specialAssistance, idSpecialist=idSpecialistInstance)
                orderProcedure.save()
            else:
                raise Exception("El especialista no existe")
        else:
            orderProcedure = models.OrderProcedure(idOrder=idOrderInstance, idProcedure=idProcedureInstance, amount=amount, frequency=frequency, item=numItem, specialAssistance=specialAssistance, idSpecialist = None)
            orderProcedure.save()
    else:
        raise Exception("La orden o el procedimiento no existen")


# ------------------------------------- PATIENT INFO
def getBasicInfoPatient(patientId):
    try:
        patient = models.Patient.objects.get(id=patientId)
        clinicalHistory = getMedicalRecords(patientId)
        return patient, clinicalHistory
    except models.Patient.DoesNotExist:
        raise Exception("El paciente no existe")
    except Exception as e:
        raise Exception("Ha ocurrido un error: " + str(e))

def getOrdersByPatient(idPatient):
    try:
        orders = models.Order.objects.filter(patientId=idPatient)
        orders = orders.prefetch_related('orderMedication_Order', 'orderProcedure_Order', 'orderDiagnositcAid_Order')
        if orders:
            return orders
        else:
            raise Exception("No hay ordenes registradas para el paciente")
    except Exception as e:
        raise Exception("Ocurrio un error al obtener las ordenes: " + str(e))