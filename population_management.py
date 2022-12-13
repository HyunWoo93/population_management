import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import numpy as np
import pandas as pd

form_class = uic.loadUiType("population_management.ui")[0]
form_inputDialog = uic.loadUiType("member_input_dialog.ui")[0]

class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.group_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # laod file data
        try:
            self.members_df = pd.read_csv('./members.csv')
            tmp_df = pd.DataFrame({'selection': [False for i in range(self.members_df.shape[0])]})
            self.members_df = pd.concat([self.members_df, tmp_df], axis = 1)
            self.update_member_table()

        # if no file, create empty dataframe
        except:
            print('No file exists.')
            self.members_df = pd.DataFrame()



        self.adding_button.clicked.connect(self.add_member)
        self.removing_button.clicked.connect(self.remove_members)
        self.deciding_button.clicked.connect(self.decide_attending_members)
        self.reset_button.clicked.connect(self.reset_attending_members)
        self.member_table.cellClicked.connect(self.update_selection)
        self.group_table.cellClicked.connect(self.update_leader)
        self.grouping_button.clicked.connect(self.update_group)



    def add_member(self) :
        self.member_input_dialog = MemberInputClass(self)
        self.member_input_dialog.show()

    def remove_members(self) :
        idx = self.members_df[self.members_df['selection'] == True].index
        self.members_df = self.members_df.drop(idx).reset_index(drop=True)
        self.update_member_table() 

    def decide_attending_members(self) :
        
        reply = QMessageBox.question(self, 'Message', '참석 인원을 확정하겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:  
            idx = self.members_df[self.members_df['selection'] == True].index
            self.attending_members = self.members_df.iloc[idx,:].reset_index(drop=True)
            tmp_df = pd.DataFrame({'group': [0 for i in range(self.attending_members.shape[0])]})
            self.attending_members = pd.concat([tmp_df, self.attending_members], axis = 1)
            self.attending_members = self.attending_members.replace({'selection':True}, False)
            

            self.update_group_table()
            self.leaders = []
        else :
            pass


    def reset_attending_members(self) :
        self.attending_members.set_index('ID', inplace = True)
        self.attending_members.update(self.members_df.set_index('ID')['value'])
        self.attending_members.reset_index(inplace = True)
        self.attending_members = self.attending_members[['group', 'ID', 'name', 'sex', 'value', 'selection']]
        self.attending_members.loc[:, 'group'] = 0
        self.attending_members.loc[:, 'selection'] = False
        self.leaders = []

        self.update_group_table()


    def update_selection(self, row, col) :
        if col is self.members_df.shape[1]-1 :
            self.members_df.iloc[row,col] = not self.members_df.iloc[row,col]
            self.member_table.setItem(row, col,  QTableWidgetItem(str(self.members_df.iloc[row,col])))
        else :
            pass

    def update_leader(self, row, col) :
        if col is self.attending_members.shape[1]-1 :
            self.attending_members.iloc[row,col] = not self.attending_members.iloc[row,col]    
            if self.attending_members.iloc[row,col]:
                self.leaders.append(self.attending_members['ID'][row])
                for idx, ID in enumerate(self.leaders) :
                    index = self.attending_members[self.attending_members['ID'] == ID].index
                    self.attending_members.loc[index, 'group'] = idx + 1
            else :
                try:
                    self.attending_members['group'][row] = 0
                    self.leaders.remove(self.attending_members['ID'][row])
                    for idx, ID in enumerate(self.leaders) :
                        index = self.attending_members[self.attending_members['ID'] == ID].index
                        self.attending_members.loc[index, 'group'] = idx + 1
                except:
                    print('ID is not in the "leaders" list.')

            self.update_group_table()

        else :
            pass

    def update_group(self) :
        while True in (self.attending_members['group'] == 0).values.tolist() :
            for idx, ID in enumerate(self.leaders) :
                index = self.attending_members[self.attending_members['ID'] == ID].index
                leader_sex = self.attending_members.loc[index,'sex'].values[0]
                leader_value = self.attending_members.loc[index,'value'].values[0]

                tmp_df = self.attending_members[self.attending_members['group'] == 0].set_index('ID')
                tmp_df['sex'] = tmp_df['sex'] - leader_sex
                tmp_df['value'] = tmp_df['value'] - leader_value
                distance = tmp_df['sex']*tmp_df['sex'] + tmp_df['value']*tmp_df['value']
                try:
                    selected_ID = distance.sort_values(ascending = False).head(1).index.values[0]
                    id_idx = self.attending_members[self.attending_members['ID'] == selected_ID].index
                    self.attending_members.loc[id_idx, 'group'] = idx + 1
                except :
                    pass
                
        self.update_value()



    def update_value(self) :
        for ID in self.leaders :
            leader_idx = self.attending_members[self.attending_members['ID'] == ID].index
            group = self.attending_members.loc[leader_idx, 'group'].values[0]
            group_idx = self.attending_members['group'] == group
            self.attending_members.loc[group_idx, 'value'] = self.attending_members.loc[group_idx, 'value']*(1/4) + self.attending_members.loc[leader_idx, 'value'].values[0]*(3/4)

        self.attending_members.sort_values(by = ['group', 'selection', 'value', 'sex'], ascending = [True, False, True, True], inplace = True)
        self.update_group_table()


    def update_member_table(self) :
        self.member_table.setRowCount(self.members_df.shape[0])
        self.member_table.setColumnCount(self.members_df.shape[1])
        tmp_df = self.members_df.replace({'sex':{0:'남', 1:'여'}})
        for i in range(self.members_df.shape[0]):
            for j in range(self.members_df.shape[1]):
                self.member_table.setItem(i, j,  QTableWidgetItem(str(tmp_df.iloc[i,j])))

    def update_group_table(self) :
        self.group_table.setRowCount(self.attending_members.shape[0])
        self.group_table.setColumnCount(self.attending_members.shape[1])
        tmp_df = self.attending_members.replace({'sex':{0:'남', 1:'여'}})
        for i in range(self.attending_members.shape[0]):
            for j in range(self.attending_members.shape[1]):
                self.group_table.setItem(i, j,  QTableWidgetItem(str(tmp_df.iloc[i,j])))

    def save_members_df(self) :
        print(self.members_df.iloc[:,:self.members_df.shape[1]-1])
        self.members_df.set_index('ID', inplace = True)
        self.members_df.update(self.attending_members.set_index('ID'))
        self.members_df.reset_index(inplace = True)
        print(self.members_df.iloc[:,:self.members_df.shape[1]-1])
        self.members_df.iloc[:,:self.members_df.shape[1]-1].to_csv('./members.csv', index = False)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',"변경된 데이터를 저장하고 종료하겠습니까?",  QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.save_members_df()
            event.accept()
        else:
            event.accept()


class MemberInputClass(QDialog, QWidget, form_inputDialog) :
    def __init__(self, mainwindow) :
        super().__init__()
        self.setupUi(self)
        self.parent_ob = mainwindow

        self.ok_button.clicked.connect(self.get_info)

    def get_info(self) :
        try:
            ID = max(self.parent_ob.members_df['ID'].tolist()) + 1
            val = max(self.parent_ob.members_df['value'].tolist()) + 1
        except :
            ID = 1
            val = 1
        name = self.name_lineEdit.text()
        sex =  self.gender_comboBox.currentIndex()
        new_member = pd.DataFrame(data = [[ID, name, sex, val, False]], columns = ['ID', 'name', 'sex', 'value','selection'])
        self.parent_ob.members_df = pd.concat([self.parent_ob.members_df, new_member], ignore_index = True)
        self.parent_ob.update_member_table()



if __name__ == "__main__" :
    app = QApplication(sys.argv) 
    myWindow = WindowClass()    
    myWindow.show()
    sys.exit(app.exec_())