#!/usr/bin/env python
# -*- coding: utf- -*-

# documentation:

import pickle
from pprint import pprint
from datetime import datetime

# Import the Canvas class
from canvasapi import Canvas


try:
    from local_settings import *
    local_settings_exists = True
except ImportError:
    local_settings_exists = False

# Canvas API URL
API_URL = "https://canvas.uva.nl"

# Initialize a new Canvas object
canvas = Canvas(API_URL, TOKEN)



def main():

    InfTheory = canvas.get_course(2205)

    InfTheory.users = {}
    users = InfTheory.get_users(include=['test_student'])
    for user in users:
        InfTheory.users[user.id] = user

    assignment_groups = InfTheory.get_assignment_groups()
    for assignment_group in assignment_groups:
        print(assignment_group)

    # Reading Questions, Intro Quizzes, Team Quizzes (11759)
    assignments = InfTheory.get_assignments(assignment_group_id=11759)

    for assignment in assignments:
        submissions = assignment.get_submissions()
        for submission in submissions:
            if submission.missing is False and submission.excused is not True and submission.workflow_state == 'unsubmitted':
                msg = "user {} has not submitted {}, changing grade to missing".format(InfTheory.users[submission.user_id], assignment)
                print(msg)
                submission.edit(submission={'late_policy_status': 'missing'}, comment={'text_comment': 'automatic tool: ' + msg})
                print(submission.workflow_state)


    return True





if __name__ == "__main__":
    main()

