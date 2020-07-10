# noinspection PyUnresolvedReferences
from DBConnection.MongoDBConnection import MongoDB

with MongoDB() as mongo:
    statisticsList = []
    i = 0
    for trace in mongo.query('PatientTrace', query = {}, projection = {'appointments': 1}):
        statistics = {}
        statistics['total_appointments'] = len(trace['appointments'])

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
            dict["elapsed_time"] = dict["second_appointment"] - dict["first_appointment"]
            statistics['elapsed_time_between_appointments'].append(dict)

        statisticsList.append(statistics)

        i += 1
        if i % 500 == 0:
            mongo.insert('PatientStatistic', statisticsList, many = True)
            statisticsList = []

    mongo.insert('PatientStatistic', statisticsList, many=True)
