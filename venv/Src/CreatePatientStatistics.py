# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB
from datetime import datetime, date

with MongoDB() as mongo:
    statisticsList = []
    i = 0
    for trace in mongo.query('PatientTrace', query = {}, projection = {'Pac_Unif_Cod': 1, 'appointments': 1}):
        statistics = {}
        statistics['pac_unif_cod'] = trace['Pac_Unif_Cod']
        statistics['total_appointments'] = len(trace['appointments'])

        statistics['visit_type_appointments'] = {}
        statistics['visit_type_appointments']['first'] = sum([1 for appointment in trace['appointments'] if appointment['Visit type'] == 'First'])
        statistics['visit_type_appointments']['revision'] = sum([1 for appointment in trace['appointments'] if appointment['Visit type'] == 'Revision'])
        statistics['visit_type_appointments']['non_presential'] = sum([1 for appointment in trace['appointments'] if appointment['Visit type'] == 'Non-presential'])
        statistics['visit_type_appointments']['other'] = sum([1 for appointment in trace['appointments'] if appointment['Visit type'] == 'Special'])

        statistics['character_of_visit_appointments'] = {}
        statistics['character_of_visit_appointments']['ordinary'] = sum([1 for appointment in trace['appointments'] if appointment['Character of visit'] == 'Ordinary'])
        statistics['character_of_visit_appointments']['preferential'] = sum([1 for appointment in trace['appointments'] if appointment['Character of visit'] == 'Preferential'])
        statistics['character_of_visit_appointments']['non_presential'] = sum([1 for appointment in trace['appointments'] if appointment['Character of visit'] == 'Non-presential'])
        statistics['character_of_visit_appointments']['results'] = sum([1 for appointment in trace['appointments'] if appointment['Character of visit'] == 'Results'])
        statistics['character_of_visit_appointments']['extra'] = sum([1 for appointment in trace['appointments'] if appointment['Character of visit'] == 'Extra'])

        statistics['visit_status_appointments'] = {}
        statistics['visit_status_appointments']['done'] = sum([1 for appointment in trace['appointments'] if appointment['Visit status'] == 'Done'])
        statistics['visit_status_appointments']['no_show_up'] = sum([1 for appointment in trace['appointments'] if appointment['Visit status'] == 'NoShowUp'])
        statistics['visit_status_appointments']['cancelled'] = sum([1 for appointment in trace['appointments'] if appointment['Visit status'] == 'Cancelled HS' or appointment['Visit status'] == 'Cancelled Pat'])
        statistics['visit_status_appointments']['other'] = sum([1 for appointment in trace['appointments'] if appointment['Visit status'] == 'Other'])

        trace['appointments'] = sorted(trace['appointments'], key=lambda k: k['Visit day'])

        if statistics['total_appointments'] != 0:
            statistics['start_to_end_appointment_diff'] = trace['appointments'][statistics['total_appointments'] - 1]['Visit day'] - trace['appointments'][0]['Visit day']

        statistics['elapsed_time_between_appointments'] = []
        for i in range(0, statistics['total_appointments'] - 1):
            dict = {}
            dict["first_appointment"] = trace['appointments'][i]['Visit day']
            dict["second_appointment"] = trace['appointments'][i+1]['Visit day']
            dict["elapsed_time"] = (date.fromtimestamp(int(dict["second_appointment"]/1000)) - date.fromtimestamp(int(dict["first_appointment"]/1000))).days
            statistics['elapsed_time_between_appointments'].append(dict)

        statistics['elapsed_time_between_appointments_without_cancelled'] = []
        k = 0
        while k < statistics['total_appointments']:
            dict = {}
            if not (trace['appointments'][k]['Visit status'] == "Cancelled Pat" or trace['appointments'][k]['Visit status'] == "Cancelled HS"):
                j = k + 1
                while j < statistics['total_appointments']:
                    if not (trace['appointments'][j]['Visit status'] == "Cancelled Pat" or trace['appointments'][j]['Visit status'] == "Cancelled HS"):
                        dict["first_appointment"] = trace['appointments'][k]['Visit day']
                        dict["second_appointment"] = trace['appointments'][j]['Visit day']
                        dict["elapsed_time"] = (date.fromtimestamp(int(dict["second_appointment"] / 1000)) -
                                                date.fromtimestamp(int(dict["first_appointment"] / 1000))).days
                        statistics['elapsed_time_between_appointments_without_cancelled'].append(dict)

                        k = j - 1
                        break
                    j += 1
            k += 1

        statisticsList.append(statistics)

        i += 1
        if i % 500 == 0:
            mongo.insert('PatientStatistic', statisticsList, many = True)
            statisticsList = []

    mongo.insert('PatientStatistic', statisticsList, many=True)
