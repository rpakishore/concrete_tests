import re, os
from datetime import datetime
import pdfplumber
import pandas as pd
from concrete_tests.helper_class import CompanyPatterns, TestData
    
class concrete_test():
    def __init__(self, file: str):
        self.file = file
        with pdfplumber.open(file) as pdf:
            data = []
            for i in range(len(pdf.pages)):
                page = pdf.pages[i]
                data.append(page.extract_text())
            self.data = "\n".join(data)
            

        self.find_company()

        self.test_data_cols = ['Specimen','Cure','Test_Date', 'Age', 'Compressive_Str']
        self.extracted_data = {
            "Filename": os.path.basename(file),
            "Filepath": file,
            "Company": self.company,
            "Report Date": None,
            "Test Data": pd.DataFrame(columns=self.test_data_cols),
            "Set Num": None,
            "Specimens": 0,
            "Cast Date": None,
            "Transported Date": None,
            "Specified Strength": None,
            "Specified Strength Days": None,
            "Admixtures": [],
            "Mix Number": None,
            "Load Vol": None,
            "Slump": None,
            "Specified Slump": [],
            "Air": None,
            "Specified Air": [],
            "Location Comments": [],
            "Other Comments": [],
            "Report Date": None,
            "Errors": pd.DataFrame(columns=['Error Code', 'Description'])
        }
        self.errors = pd.DataFrame(columns=['Error Code', 'Description'])
        
        company_patterns = self._init_company_patterns()
        
        for company_pattern in company_patterns:
            if self.company and self.company == company_pattern.name:
                try:
                    self.extracted_data = _parse_pdf(self.data, company_pattern, self.errors)
                except Exception as e:
                    self.extracted_data = TestData()
                    self.log_error('z',str(e))
                self.extracted_data.company = self.company
                self.extracted_data.filepath = file
                self.extracted_data.filename = os.path.basename(file)
                
                self._check_errors()
                break

        if self.company:
            if self.company == "McElhanney":
                self.McElhanney()
            if self.company == "Kontur Geotechnical Consultants":
                self.Kontur()
            self._check_errors()
        else:
            self.log_error('a',self.data.split('\n')[0].strip())

        self.extracted_data.errors = self.errors
    def combine_sheets(self, combine):
        for key in combine.keys():
            if self.extracted_data['Mix Number'] in combine[key]:
                self.extracted_data['Mix Number'] = key

    def find_company(self):
        company = None
        if 'mcelhanney' in self.data.split('\n')[0].lower():
            company = "McElhanney"
        if 'kontur' in self.data.split('\n')[0].lower():
            company = "Kontur Geotechnical Consultants"
        self.company = company
        return company
    
    def log_error(self, code, desc):
        df = pd.DataFrame([[code, desc]],columns = ['Error Code', 'Description'])
        self.errors = pd.concat([self.errors, df], ignore_index=True)
        
    def _check_errors(self):
        self.err = {
            'a':'Template for this company is not defined',
            'b': 'Specimen # in extracted PDF does not match scrapped test data from PDF',
            'c': 'Slump issue',
            'd': 'Air % Issue',
            'e': 'Missing Information',
            'z': 'Some other error'
        }
        data = self.extracted_data
        if len(data.data) != data.specimen:
            self.log_error('b', f"Specimens: {data.specimen}, Avail. Data: {len(data.data)}")

        if data.air and data.specified_air != []:
            if data.air > data.specified_air[1]:
                self.log_error('d', f"Air: {data.air}% > Allow. max:{data.specified_air[1]}%")
            elif data.air < data.specified_air[0]:
                self.log_error('d', f"Air: {data.air}% < Allow. min:{data.specified_air[0]}%")
        else:
            self.log_error('e', 'No Air content data found.')

        if data.slump and data['Specified Slump'] != []:
            if data.slump > data.specified_slump[1]:
                self.log_error('c', f"Slump: {data.slump}mm > Allow. max:{data.specified_slump[1]}mm")
            elif data.slump < data.specified_slump[0]:
                self.log_error('c', f"Slump: {data.slump}mm <  Allow. min:{data.specified_slump[0]}mm")
        else:
            self.log_error('e', 'Slump info not found.')
        self.extracted_data = data
        
    def _init_company_patterns(self):
        self.McElhanney = CompanyPatterns(
        name="McElhanney",
        test_data=r".*([A-Z]) *Cylinder *(Lab|Field) *(\d*) *((\d{2}-\w{3})-? *(\d*) *[A-Za-z ]*)?\d{3}.\d *\d{3}.\d( *\d* *(\d*.\d))?",
        specified_str= r"SPECIFIED STRENGTH\s*(\d*)MPa *@ *(\d*) DAYS",
        set_data=  r".*SET *NO.(\d*) *SPECIMENS *(\d*) *CAST *(\d{2}-\w{3}-\d{4}) *TRANSPORTED *(\d{2}-\w{3}-\d{4})",
        report_date= r".*Page *1 *of *\d* *(\d{4}.\w{3}.\d*)|(\d*-\w{3}-\d{4})",
        air= r".*AIR *(\d{1,2}.?\d?) *% *SPEC. *(\d{1,2}.?\d?) *± *(\d{1,2}.?\d?)",
        slump= r".*SLUMP *(\d*) *mm *SPEC. *(\d*) *± *(\d*)",
        mix= r".*MIX *NO. *(.*)$",
        volume= r"^LOAD *VOL. *(\d*) m3"
        )
        
        self.Kontur = CompanyPatterns(
        name="Kontur Geotechnical Consultants",
        test_data= r"([A-Z]) *Cylinder *(\d*) *(Lab|Field) *((\d{2}-\w{3})|(\w{3}.\d{2})-? *(\d*) *[A-Za-z ]*)?\d{3}.\d *\d{3}.\d( *\d* *(\d*.\d))?",
        specified_str= r"SPECIFIED *STRENGTH: *(\d*) *MPa *@ *(\d*) * DAYS",
        set_data=  r"SET *NO.:(\d*) *SPECIMENS: *(\d*) *CAST: *(\d{4}.\w{3}.\d{2}) *TRANSPORTED: *(\d{4}.\w{3}.\d{2})",
        report_date= r".*Page *1 *of *\d* *(\d*.\w{3}.\d*)|(\d*-\w{3}-\d{4})",
        air= r".*AIR: *(\d{1,2}.?\d?) *% *SPEC.: *(\d{1,2}.?\d?) *± *(\d{1,2}.?\d?)",
        slump= r".*SLUMP: *(\d*) *mm *SPEC.: *(\d*) *± *(\d*)",
        mix= r".*MIX *NO.:? *(.*)$",
        volume= r"^LOAD *VOL.: *(\d*) m3"
        )
        return (self.McElhanney, self.Kontur)

    def McElhanney(self):
        try:
            pattern = {
                "Test Data": r".*([A-Z]) *Cylinder *(Lab|Field) *(\d*) *((\d{2}-\w{3})-? *(\d*) *[A-Za-z ]*)?\d{3}.\d *\d{3}.\d( *\d* *(\d*.\d))?",
                "Specified Strength": r"SPECIFIED STRENGTH\s*(\d*)MPa *@ *(\d*) DAYS",
                "Set Data": r".*SET *NO.(\d*) *SPECIMENS *(\d*) *CAST *(\d{2}-\w{3}-\d{4}) *TRANSPORTED *(\d{2}-\w{3}-\d{4})",
                "Report Date": r".*Page *1 *of *\d* *(\d{4}.\w{3}.\d*)|(\d*-\w{3}-\d{4})",
                "Air": r".*AIR *(\d{1,2}.?\d?) *% *SPEC. *(\d{1,2}.?\d?) *± *(\d{1,2}.?\d?)",
                "Slump": r".*SLUMP *(\d*) *mm *SPEC. *(\d*) *± *(\d*)",
                "Mix": r".*MIX *NO. *(.*)$",
                "Load Volume": r"^LOAD *VOL. *(\d*) m3"
            }
            

            for i, line in enumerate(self.data.split('\n')):
                specified_strength = re.match(pattern['Specified Strength'], line.strip())
                if specified_strength:
                    self.extracted_data["Specified Strength"] = int(specified_strength.group(1))
                    self.extracted_data["Specified Strength Days"] = int(specified_strength.group(2))

                set_data = re.match(pattern["Set Data"], line)
                if set_data:
                    self.extracted_data["Set Num"] = set_data.group(1)
                    self.extracted_data["Specimens"] = int(set_data.group(2))
                    self.extracted_data["Cast Date"] = datetime.strptime(set_data.group(3),"%d-%b-%Y")
                    self.extracted_data["Transported Date"] = datetime.strptime(set_data.group(4),"%d-%b-%Y")
                    continue

                test_data = re.match(pattern["Test Data"], line)
                if test_data:
                    data = [test_data.group(1), test_data.group(2), test_data.group(5), test_data.group(6), test_data.group(8)]
                    if data[2]:
                        if datetime.strptime(data[2] + "-" +str(datetime.now().year), "%d-%b-%Y") > datetime.now():
                            data[2] = datetime.strptime(data[2] + "-" +str(datetime.now().year - 1), "%d-%b-%Y")
                        else:
                            data[2] = datetime.strptime(data[2] + "-" +str(datetime.now().year), "%d-%b-%Y")
                    df = pd.DataFrame([data],columns = self.test_data_cols)
                    self.extracted_data['Test Data'] = pd.concat([self.extracted_data['Test Data'], df], ignore_index=True)
                    continue
                
                report_date = re.match(pattern['Report Date'], line)
                if report_date:
                    if report_date.group(1):
                        self.extracted_data['Report Date'] = datetime.strptime(report_date.group(1),"%Y.%b.%d")
                    else:
                        self.extracted_data['Report Date'] = datetime.strptime(report_date.group(2),"%d-%b-%Y")
                    continue

                air = re.match(pattern['Air'], line)
                if air:
                    self.extracted_data['Air'] = float(air.group(1))
                    self.extracted_data['Specified Air'] = [float(air.group(2))-float(air.group(3)), float(air.group(2))+float(air.group(3))]
                    continue

                if line.lower().strip().startswith('admixtures (ml/m'):
                    for j in range(i, len(self.data.split('\n'))):
                        if self.data.split('\n')[j].lower().strip().startswith('curing conditions'):
                            self.extracted_data['Admixtures'] = self.data.split('\n')[i+1:j]
                            break
                    continue

                if line.lower().strip() == "location":
                    for j in range(i, len(self.data.split('\n'))):
                        if self.data.split('\n')[j].lower().strip().startswith('supplier'):
                            self.extracted_data['Location Comments'] = self.data.split('\n')[i+1:j]
                            break
                    continue

                if line.lower().strip() == "comments":
                    for j in range(i, len(self.data.split('\n'))):
                        if self.data.split('\n')[j].lower().strip().startswith('load'):
                            self.extracted_data['Other Comments'] = self.data.split('\n')[i+1:j]
                            break
                    continue
                
                slump = re.match(pattern['Slump'], line)
                if slump:
                    self.extracted_data['Slump'] = int(slump.group(1))
                    self.extracted_data['Specified Slump'] = [int(slump.group(2))-int(slump.group(3)),int(slump.group(2))+int(slump.group(3))]
                    continue

                mix = re.match(pattern['Mix'], line)
                if mix:
                    self.extracted_data['Mix Number'] = mix.group(1)
                    continue

                load = re.match(pattern['Load Volume'], line.strip())
                if load:
                    self.extracted_data['Load Vol'] = float(load.group(1))

        except Exception as e:
            self.log_error('z',str(e))

    def Kontur(self):
        try:
            pattern = {
                "Test Data": r"([A-Z]) *Cylinder *(\d*) *(Lab|Field) *((\d{2}-\w{3})|(\w{3}.\d{2})-? *(\d*) *[A-Za-z ]*)?\d{3}.\d *\d{3}.\d( *\d* *(\d*.\d))?",
                "Specified Strength": r"SPECIFIED *STRENGTH: *(\d*) *MPa *@ *(\d*) * DAYS",
                "Set Data": r"SET *NO.:(\d*) *SPECIMENS: *(\d*) *CAST: *(\d{4}.\w{3}.\d{2}) *TRANSPORTED: *(\d{4}.\w{3}.\d{2})",
                "Report Date": r".*Page *1 *of *\d* *(\d*.\w{3}.\d*)|(\d*-\w{3}-\d{4})",
                "Air": r".*AIR: *(\d{1,2}.?\d?) *% *SPEC.: *(\d{1,2}.?\d?) *± *(\d{1,2}.?\d?)",
                "Slump": r".*SLUMP: *(\d*) *mm *SPEC.: *(\d*) *± *(\d*)",
                "Mix": r".*MIX *NO.:? *(.*)$",
                "Load Volume": r"^LOAD *VOL.: *(\d*) m3"
            }

            for i, line in enumerate(self.data.split('\n')):
                specified_strength = re.match(pattern['Specified Strength'], line.strip())
                if specified_strength:
                    self.extracted_data["Specified Strength"] = int(specified_strength.group(1))
                    self.extracted_data["Specified Strength Days"] = int(specified_strength.group(2))

                set_data = re.match(pattern["Set Data"], line)
                if set_data:
                    self.extracted_data["Set Num"] = set_data.group(1)
                    self.extracted_data["Specimens"] = int(set_data.group(2))
                    self.extracted_data["Cast Date"] = datetime.strptime(set_data.group(3),"%Y.%b.%d")
                    self.extracted_data["Transported Date"] = datetime.strptime(set_data.group(4),"%Y.%b.%d")
                    continue

                test_data = re.match(pattern["Test Data"], line)
                if test_data:
                    data = [test_data.group(1), test_data.group(3), test_data.group(6), test_data.group(7), test_data.group(9)]
                    if data[2]:
                        if datetime.strptime(data[2] + "-" +str(datetime.now().year), "%b.%d-%Y") > datetime.now():
                            data[2] = datetime.strptime(data[2] + "-" +str(datetime.now().year - 1), "%b.%d-%Y")
                        else:
                            data[2] = datetime.strptime(data[2] + "-" +str(datetime.now().year), "%b.%d-%Y")
                    df = pd.DataFrame([data],columns = self.test_data_cols)
                    self.extracted_data['Test Data'] = pd.concat([self.extracted_data['Test Data'], df], ignore_index=True)
                    continue
                
                report_date = re.match(pattern['Report Date'], line)
                if report_date:
                    if report_date.group(1):
                        self.extracted_data['Report Date'] = datetime.strptime(report_date.group(1),"%Y.%b.%d")
                    else:
                        self.extracted_data['Report Date'] = datetime.strptime(report_date.group(2),"%d-%b-%Y")
                    continue

                air = re.match(pattern['Air'], line)
                if air:
                    self.extracted_data['Air'] = float(air.group(1))
                    self.extracted_data['Specified Air'] = [float(air.group(2))-float(air.group(3)), float(air.group(2))+float(air.group(3))]
                    continue

                if line.lower().strip().startswith('admixtures'):
                    for j in range(i, len(self.data.split('\n'))):
                        if self.data.split('\n')[j].lower().strip().startswith('curing'):
                            self.extracted_data['Admixtures'] = self.data.split('\n')[i+1:j]
                            break
                    continue

                if line.lower().strip() == "location:":
                    for j in range(i, len(self.data.split('\n'))):
                        if self.data.split('\n')[j].lower().strip().startswith('supplier'):
                            self.extracted_data['Location Comments'] = self.data.split('\n')[i+1:j]
                            break
                    continue

                if line.lower().strip() == "comments:":
                    for j in range(i, len(self.data.split('\n'))):
                        if self.data.split('\n')[j].lower().strip().startswith('load'):
                            self.extracted_data['Other Comments'] = self.data.split('\n')[i+1:j]
                            break
                    continue
                
                slump = re.match(pattern['Slump'], line)
                if slump:
                    self.extracted_data['Slump'] = int(slump.group(1))
                    try:
                        self.extracted_data['Specified Slump'] = [int(slump.group(2))-int(slump.group(3)),int(slump.group(2))+int(slump.group(3))]
                    except:
                        self.extracted_data['Specified Slump'] = []
                    continue

                mix = re.match(pattern['Mix'], line)
                if mix:
                    self.extracted_data['Mix Number'] = mix.group(1)
                    continue

                load = re.match(pattern['Load Volume'], line.strip())
                if load:
                    try:
                        self.extracted_data['Load Vol'] = float(load.group(1))
                    except:
                        self.log_error('e', 'Missing information on Load volume')

        except Exception as e:
            self.log_error('z',str(e))
            
def _parse_pdf(data:str, pattern: CompanyPatterns, errors: pd.DataFrame) -> TestData:
    for i, line in enumerate(data.split('\n')):
        
        #Parse specified str data
        specified_strength = re.match(pattern.specified_str, line.strip())
        if specified_strength:
            specified_str = int(specified_strength.group(1))
            specified_str_days = int(specified_strength.group(2))
        
        #Parse set data
        set_data = re.match(pattern.set_data, line)
        if set_data:
            set_num = set_data.group(1)
            specimen = int(set_data.group(2))
            cast_date = datetime.strptime(set_data.group(3),"%Y.%b.%d")
            transport_date = datetime.strptime(set_data.group(4),"%Y.%b.%d")
            continue
        
        #Parse Test data
        test_data = re.match(pattern.test_data, line)
        if test_data:
            test_data_cols = ['Specimen','Cure','Test_Date', 'Age', 'Compressive_Str']
            data = [test_data.group(1), test_data.group(3), test_data.group(6), test_data.group(7), test_data.group(9)]
            if data[2]:
                if datetime.strptime(data[2] + "-" +str(datetime.now().year), "%b.%d-%Y") > datetime.now():
                    data[2] = datetime.strptime(data[2] + "-" +str(datetime.now().year - 1), "%b.%d-%Y")
                else:
                    data[2] = datetime.strptime(data[2] + "-" +str(datetime.now().year), "%b.%d-%Y")
            df = pd.DataFrame([data],columns = test_data_cols)
            data = pd.concat([data, df], ignore_index=True)
            continue
        
        #Get report date
        report_date = re.match(pattern.report_date, line)
        if report_date:
            if report_date.group(1):
                report_date = datetime.strptime(report_date.group(1),"%Y.%b.%d")
            else:
                report_date = datetime.strptime(report_date.group(2),"%d-%b-%Y")
            continue
        
        #Get aircontent
        air = re.match(pattern.air, line)
        if air:
            air = float(air.group(1))
            specified_air = [float(air.group(2))-float(air.group(3)), float(air.group(2))+float(air.group(3))]
            continue
        
        #Admixtures
        if line.lower().strip().startswith('admixtures (ml/m'):
            for j in range(i, len(data.split('\n'))):
                if data.split('\n')[j].lower().strip().startswith('curing conditions'):
                    admixtures = data.split('\n')[i+1:j]
                    break
            continue
        
        #Location Comments
        if line.lower().strip() == "location":
            for j in range(i, len(data.split('\n'))):
                if data.split('\n')[j].lower().strip().startswith('supplier'):
                    location_comments = data.split('\n')[i+1:j]
                    break
            continue
        
        #Other Comments
        if line.lower().strip() == "comments":
            for j in range(i, len(data.split('\n'))):
                if data.split('\n')[j].lower().strip().startswith('load'):
                    other_comments = data.split('\n')[i+1:j]
                    break
            continue
        
        slump = re.match(pattern.slump, line)
        if slump:
            slump = int(slump.group(1))
            specified_slump = [int(slump.group(2))-int(slump.group(3)),int(slump.group(2))+int(slump.group(3))]
            continue

        mix = re.match(pattern.mix, line)
        if mix:
            mix_num = mix.group(1)
            continue

        load = re.match(pattern.volume, line.strip())
        if load:
            load_vol = float(load.group(1))
            
    return TestData(
        report_date =report_date,
        data =data,
        set_num =set_num,
        specimen =specimen,
        cast_date =cast_date,
        transport_date =transport_date,
        specified_str =specified_str,
        specified_str_days =specified_str_days,
        admixtures =admixtures,
        mix_num =mix_num,
        load_vol =load_vol,
        slump =slump,
        specified_slump =specified_slump,
        air =air,
        specified_air =specified_air,
        location_comments =location_comments,
        other_comments =other_comments,
        errors=errors
        )
