import unittest
from model_service import FEATURE_COLUMNS, prepare_feature_frame

class ModelServiceTests(unittest.TestCase):
    def test_expected_columns_and_conversion(self):
        payload={"hemo":"12.5","al":"1","sg":"1.020","sc":"1.3","pcv":"35","htn":"yes"}
        frame=prepare_feature_frame(payload)
        self.assertEqual(list(frame.columns), FEATURE_COLUMNS)
        self.assertEqual(float(frame.loc[0,"hemo"]),12.5)
        self.assertEqual(int(frame.loc[0,"htn"]),1)

if __name__ == "__main__": unittest.main()
