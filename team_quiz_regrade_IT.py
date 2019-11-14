#!/usr/bin/env python
# -*- coding: utf- -*-

import pickle
from pprint import pprint
from datetime import datetime
import argparse

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

# Add parser and explanation for command-line arguments
parser = argparse.ArgumentParser(description="Regrade a team quiz by assigning the grade from one team member to all team members.")
parser.add_argument('quiz',type=int,help='number to indicate which team quiz to regrade (1--7)')
parser.add_argument('-d','--dry_run',action='store_true',help='do a dry run (compute grades but do not upload them)')
parser.add_argument('-n','--nice',action='store_true', help='be nice by only increasing a student\'s grade')
parser.add_argument('-i','--ignore',nargs='*',default='[]',help='type all student names within quotes, separated by spaces')


def assign_same_grade(teams, assignment, dry_run=False, be_nice=False, ignore_list=[]):

    for team in teams:
        if len(team.submissions) == 0:
            continue

        # try to figure out if regrading has already been run by looking through this team's announcements
        if team.id > 0:
            group_announcements = team.get_discussion_topics(only_announcements=True)
            already_regraded = False
            for group_announcement in group_announcements:
                if group_announcement.title == 'log of automatic regrading of {}'.format(assignment.name):
                    already_regraded = True

            if already_regraded:
                print('announcement log found! Regrading of {} has already been performed for team {}. Skipping the '
                      'script for this team. Delete the announcement log in order to run the script '
                      'nevertheless.'.format(
                        assignment.name, team.name))
                continue  # with next team

        message = "\nlog of automatic team_quiz regrading tool, run at {}\n".format(datetime.now())
        message += "Team: {} submissions of {} (before change)\n".format(team.name, assignment.name)
        for subm in team.submissions:
            message += "student: {}, finished: {}, score: {}\n".format(subm.user.name, subm.submitted_at, subm.score)

        if team.submissions[0].user.name not in ignore_list:
            team_score = team.submissions[0].score
        else:
            team_score = team.submissions[1].score
        # team_score = team.submissions[0].score

        message += "\nIn team quizzes, all students in a team receive the same grade which is equal to the first " \
                   "submission by the team, so {}\n".format(
            team_score)
        if be_nice:
            message += "Because this quiz has been regraded (and the actual submission times lost, thanks Canvas), " \
                       "we take the maximum of all submitted scores for this quiz.\n "
            scores = []
            for subm in team.submissions:
                if subm.score is not None:
                    scores.append(subm.score)
            team_score = max(scores)

        changed = False
        for i in range(0, len(team.submissions)):
            subm = team.submissions[i]
            # if be_nice:
            #     if subm['score'] is None or float(team_score) > float(subm['score']):
            #         message += "{}'s score is changed from {} to {}\n".format(subm.user.name, subm.score, team_score)
            #         if not dry_run:
            #             comment = "automatic regrading of {}: changing {}'s score from {} to {}".format(assignment.name, subm.user.name, subm.score, team_score)
            #             subm = subm.edit(submission={'posted_grade': team_score}, comment={'text_comment': comment})
            #             # capi.grade_assignment_submission(self.course.id, assignment_id, subm['user_id'], team_score,
            #             #                                  comment="automatic regrading of {}: changing {}'s score from {} to {}".format(
            #             #                                      self.assignments[assignment_id].name,
            #             #                                      self.course.users[subm['user_id']].name, subm['score'],
            #             #                                      team_score))
            #         changed = True
            # else:
            if team_score != subm.score:
                message += "{}'s score is changed from {} to {}\n".format(subm.user.name, subm.score, team_score)
                if subm.score is not None and subm.score > team_score:
                    print("some grade has actually been lowered! {}'s score is changed from {} to {}\n".format(subm.user.name, subm.score, team_score))
                    pass
                    # raise(Exception('Some grade is actually lowered!'))
                if not dry_run:
                    comment = "automatic regrading of {}: changing {}'s score from {} to {}".format(assignment.name, subm.user.name, subm.score, team_score)
                    subm = subm.edit(submission={'posted_grade': team_score}, comment={'text_comment': comment})
                    # capi.grade_assignment_submission(self.course.id, assignment_id, subm['user_id'], team_score,
                    #                                  comment="automatic regrading of {}: changing {}'s score from {} to {}".format(
                    #                                      self.assignments[assignment_id].name,
                    #                                      self.course.users[subm['user_id']].name, subm['score'],
                    #                                      team_score))
                else:
                    # change the score locally if dry_run
                    subm.score = team_score
                changed = True

        if changed:
            message += "\nTeam: {} submissions of {} (after change)\n".format(team.name, assignment.name)
            for subm in team.submissions:
                message += "student: {}, finished: {}, score: {}\n".format(subm.user.name, subm.submitted_at, subm.score)
        else:
            message += "no changes necessary\n"
        print(message)

        message = message.replace("\n", "<br />\n")
        if team.id > 0:
            if not dry_run:
                team.create_discussion_topic(title='log of automatic regrading of {}'.format(assignment.name), message=message, is_announcement=True)

    return True


def get_team_of_user(user_id, teams, course):
    """

    :param user_id:
    :param teams:
    :param course:
    :return:
    """
    for team in teams:
        for user in team.users:
            if user.id == user_id:
                return team
    user = course.get_user(user_id)
    print('no team found for user_id: {}'.format(user))
    return None


def mySort(s):
    if s is None:
        return "not submitted"
    else:
        return s



def main():
    options = parser.parse_args()

    Course = canvas.get_course(10933)

    Course.users = {}
    users = Course.get_users()
    for user in users:
        Course.users[user.id] = user

    group_categories = Course.get_group_categories()
    group_phase = "First 3 Weeks" if options.quiz <= 3 else "Last 4 Weeks"
    for group_category in group_categories:
        if group_category.name == group_phase:
            group_category_id = group_category.id
            break

    teams = Course.get_groups()
    relevant_teams = []
    for team in teams:
        if team.group_category_id == group_category_id:
            team.users = team.get_users()
            team.submissions = []
            relevant_teams.append(team)

    for assignment in Course.get_assignments():
        if 'Team' in assignment.name:
            print(assignment.id, assignment.name)

    #Team quiz ids for assignments 1 through 7 (in that order)
    team_quizzes = list(map(Course.get_assignment, [72713,72724,72732,72739,72746,72756,72761]))
    team_quiz = team_quizzes[options.quiz-1]
    submissions = team_quiz.get_submissions(grouped=True)
    for submission in submissions:
        # if submission.workflow_state == 'graded':
        team = get_team_of_user(submission.user_id, relevant_teams, Course)
        if team is not None:
            submission.user = Course.users[submission.user_id]
            team.submissions.append(submission)

    # sort submissions per team by finished_at
    for team in relevant_teams:
        team.submissions = sorted(team.submissions, key=lambda subm: mySort(subm.submitted_at))


    assign_same_grade(relevant_teams, team_quiz, dry_run=options.dry_run, be_nice=options.nice, ignore_list=options.ignore)

    return True


    # me = canvas.get_current_user()
    # users = ModCrypto.get_users()
    # quiz = ModCrypto.get_quiz(5936)
    #
    # for item in quiz.get_all_quiz_submissions():
    #     print(item)
    #
    # return True
    #
    # try:
    #     with open('ModCrypto.pickle', 'rb') as handle:
    #         ModCrypto = pickle.load(handle)
    # except FileNotFoundError:
    #     ModCrypto = canvas.get_course(1598)
    #
    #
    #     #
    #     # ModCrypto.load_users()
    #     # ModCrypto.load_team_sets()
    #     # ModCrypto.load_teams()
    #
    #     with open('ModCrypto.pickle', 'wb') as handle:
    #         pickle.dump(ModCrypto, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # msg = "First line<br>second line<br><br>test"
    # capi.announce_to_group(18234, 'test', msg)

    # ModCrypto.get_team_set_by_name('Last 3 weeks').load_quiz(5932)





if __name__ == "__main__":
    main()
