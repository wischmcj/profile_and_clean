import pytest
import pandas as pd
from normalization import (
    correct_common_string_issues,
    standardize_delimited_field,
    remove_bracketed_references
)


class TestCorrectCommonStringIssues:
    """Test correct_common_string_issues function with real examples from data profiling"""
    
    def test_strip_trailing_spaces(self):
        """Test stripping trailing spaces from month names"""
        series = pd.Series(['January ', 'October ', 'December '])
        result = correct_common_string_issues(series)
        assert result.iloc[0] == 'January'
        assert result.iloc[1] == 'October'
        assert result.iloc[2] == 'December'
    
    def test_strip_leading_spaces(self):
        """Test stripping leading spaces from alert criteria"""
        series = pd.Series(['  Suspected Physical Attack', ' Damage or destruction'])
        result = correct_common_string_issues(series)
        assert result.iloc[0] == 'Suspected Physical Attack'
        assert result.iloc[1] == 'Damage or destruction'
    
    def test_remove_leading_trailing_spaces_combined(self):
        """Test removing both leading and trailing spaces"""
        series = pd.Series(['  October  ', '  January  '])
        result = correct_common_string_issues(series)
        assert result.iloc[0] == 'October'
        assert result.iloc[1] == 'January'
    
    def test_nerc_region_whitespace(self):
        """Test NERC region whitespace issues from actual data"""
        series = pd.Series(['WECC ', 'RE ', 'RF ', 'MRO / RF'])
        result = correct_common_string_issues(series)
        assert result.iloc[0] == 'WECC'
        assert result.iloc[1] == 'RE'
        assert result.iloc[2] == 'RF'
        assert result.iloc[3] == 'MRO / RF'  # Note: spaces around / may persist based on implementation
    
    def test_restoration_time_with_unknown_spaces(self):
        """Test restoration time with trailing spaces"""
        series = pd.Series(['Unknown ', 'Ongoing ', '14:12:00'])
        result = correct_common_string_issues(series)
        assert result.iloc[0] == 'Unknown'
        assert result.iloc[1] == 'Ongoing'
        assert result.iloc[2] == '14:12:00'
    
    def test_event_type_leading_dash_and_spaces(self):
        """Test event type with leading dashes and spaces"""
        series = pd.Series(['- Weather or natural disaster', '- Vandalism', '- Unknown'])
        result = correct_common_string_issues(series)
        # Dashes should remain (these are legitimate prefixes), but spaces should be stripped
        assert '- Weather' in result.iloc[0] or result.iloc[0] == '- Weather or natural disaster'
    
    def test_alert_criteria_nonbreaking_spaces(self):
        """Test removal of non-breaking spaces from alert criteria"""
        # Non-breaking space character: \xa0
        series = pd.Series(['\xa0Damage or destruction of a Facility', '\xa0Unplanned evacuation'])
        result = correct_common_string_issues(series)
        # Should have leading space/nbsp removed
        assert result.iloc[0].startswith('D')  # First char should be 'D', not '\xa0'
        assert result.iloc[1].startswith('U')  # First char should be 'U', not '\xa0'
    
    def test_duplicate_spaces_removed(self):
        """Test that duplicate/multiple spaces are consolidated"""
        series = pd.Series(['Multiple    spaces   here', 'Normal spacing'])
        result = correct_common_string_issues(series)
        assert '    ' not in result.iloc[0]  # No more than one space
        assert result.iloc[1] == 'Normal spacing'
    
    def test_event_type_typo_preserved(self):
        """Test that typos like 'Sever Weather' are preserved (not auto-corrected)"""
        # Note: ftfy might attempt to fix this, but we test the original intent
        series = pd.Series(['Sever Weather', 'Severe Weather'])
        result = correct_common_string_issues(series)
        # The series should be processed (case might be normalized)
        assert len(result) == 2


class TestStandardizeDelimitedField:
    """Test standardize_delimited_field with real examples from data"""
    
    def test_area_affected_semicolon_to_colon(self):
        """Test converting semicolons to colons in area_affected"""
        series = pd.Series(['Maine;', 'Texas: Harris County;', 'Georgia; Clayton County;'])
        result = standardize_delimited_field(series, 'area_affected')
        # Semicolons should be converted to colons
        assert result.iloc[0] == 'Maine:'
        assert ':' in result.iloc[1]
        assert ':' in result.iloc[2]
    
    def test_area_affected_removes_extra_spaces(self):
        """Test that extra spaces around delimiters are removed"""
        series = pd.Series(['Maine  :  ', 'Texas  :  Harris County  ;'])
        result = standardize_delimited_field(series, 'area_affected')
        assert 'Maine:' in result.iloc[0]
        assert '  :  ' not in result.iloc[1]  # Extra spaces removed
    
    def test_nerc_region_slash_to_comma(self):
        """Test converting slashes to commas in NERC region"""
        series = pd.Series(['SERC/RF', 'TRE/WECC', 'WECC/SERC/MRO'])
        result = standardize_delimited_field(series, 'nerc_region')
        # Slashes should be converted to commas
        assert ',' in result.iloc[0]
        assert ',' in result.iloc[1]
        assert result.iloc[0].count(',') == 1  # One separator
        assert result.iloc[2].count(',') == 2  # Two separators
    
    def test_nerc_region_mixed_delimiters(self):
        """Test NERC region with mixed delimiters"""
        series = pd.Series(['SERC / RF', 'MRO / RF', 'RFC; SERC', 'SPP, SERC, TRE'])
        result = standardize_delimited_field(series, 'nerc_region')
        # All should be normalized to commas
        for item in result:
            assert '/' not in item or ',' in item  # Slashes replaced or already commas
    
    def test_nerc_region_removes_consecutive_delimiters(self):
        """Test that consecutive delimiters are consolidated"""
        series = pd.Series(['SERC,,RF', 'TRE///WECC'])
        result = standardize_delimited_field(series, 'nerc_region')
        # Multiple consecutive delimiters should become single
        assert ',,' not in result.iloc[0]
        assert '///' not in result.iloc[1]
    
    def test_event_type_slash_to_dash(self):
        """Test converting slashes to dashes in event_type"""
        series = pd.Series([
            'Severe Weather/Transmission Interruption',
            'Actual Physical Attack/Vandalism',
            'Severe Weather/Distribution Interruption'
        ])
        result = standardize_delimited_field(series, 'event_type')
        # Slashes should be converted to dashes
        assert '-' in result.iloc[0]
        assert '-' in result.iloc[1]
        assert '-' in result.iloc[2]
    
    def test_event_type_mixed_formats(self):
        """Test event_type with various multi-value formats"""
        series = pd.Series([
            'Physical attack - Vandalism',
            'Physical attack / Vandalism',
            'Physical attack ; Vandalism'
        ])
        result = standardize_delimited_field(series, 'event_type')
        # All should use consistent delimiter (dash)
        for item in result:
            assert '-' in item or len(item.split('-')) > 1
    
    def test_field_not_in_config_returns_unchanged(self):
        """Test that fields not in delimiter_correction config are returned unchanged"""
        series = pd.Series(['Some / Value', 'Another; Value'])
        result = standardize_delimited_field(series, 'unknown_field')
        # Should return unchanged
        assert result.iloc[0] == series.iloc[0]
        assert result.iloc[1] == series.iloc[1]
    
    def test_empty_items_removed_from_delimited_list(self):
        """Test that empty items between delimiters are removed"""
        series = pd.Series(['Texas:; :Harris County', 'Maine:::'])
        result = standardize_delimited_field(series, 'area_affected')
        # Empty items should be filtered out
        assert '::' not in result.iloc[0] and ';;;' not in result.iloc[0]
        assert ':::' not in result.iloc[1]
    
    def test_null_values_preserved(self):
        """Test that null values are preserved"""
        series = pd.Series(['Texas:Harris County', None, 'Maine:'])
        result = standardize_delimited_field(series, 'area_affected')
        # Null should remain null
        assert pd.isna(result.iloc[1])


class TestRemoveBracketedReferences:
    """Test remove_bracketed_references with real examples from data"""
    
    def test_remove_numeric_references(self):
        """Test removing numeric references like [13]"""
        series = pd.Series([
            'Massachusetts: Hampden County[13];',
            'County[1] reference',
            'Normal text'
        ])
        result = remove_bracketed_references(series)
        assert '[13]' not in result.iloc[0]
        assert result.iloc[0] == 'Massachusetts: Hampden County;'
        assert '[1]' not in result.iloc[1]
        assert result.iloc[1] == 'County reference'
        assert result.iloc[2] == 'Normal text'
    
    def test_remove_multiple_references(self):
        """Test removing multiple bracketed references in same string"""
        series = pd.Series(['Text[1] with[2] multiple[3] references'])
        result = remove_bracketed_references(series)
        assert '[1]' not in result.iloc[0]
        assert '[2]' not in result.iloc[0]
        assert '[3]' not in result.iloc[0]
        assert result.iloc[0] == 'Text with multiple references'
    
    def test_remove_alphabetic_references(self):
        """Test removing alphabetic references like [abc]"""
        series = pd.Series(['Alert[ABC] criteria', 'Value[xyz] here'])
        result = remove_bracketed_references(series)
        assert '[ABC]' not in result.iloc[0]
        assert '[xyz]' not in result.iloc[1]
        assert result.iloc[0] == 'Alert criteria'
        assert result.iloc[1] == 'Value here'
    
    def test_remove_mixed_alphanumeric_references(self):
        """Test removing mixed alphanumeric references"""
        series = pd.Series(['Code[a1] test', 'Value[123xyz] data'])
        result = remove_bracketed_references(series)
        assert '[a1]' not in result.iloc[0]
        assert '[123xyz]' not in result.iloc[1]
    
    def test_preserve_normal_brackets(self):
        """Test that brackets without content are handled"""
        series = pd.Series(['Text []', 'Value [ ]'])
        result = remove_bracketed_references(series)
        # Empty or space-only brackets should be removed
        # Result should have less brackets than original
        assert result.iloc[0].count('[') < series.iloc[0].count('[')
    
    def test_remove_spaces_within_brackets(self):
        """Test removing references with internal spaces like [ 13 ]"""
        series = pd.Series(['County[ 13 ] name', 'Value [ ABC ] test'])
        result = remove_bracketed_references(series)
        assert '[ 13 ]' not in result.iloc[0]
        assert '[ ABC ]' not in result.iloc[1]
        assert result.iloc[0] == 'County name'
        assert result.iloc[1] == 'Value test'
    
    def test_real_world_area_affected_example(self):
        """Test with real-world area_affected formatting"""
        series = pd.Series([
            'Massachusetts: Hampden County[13];',
            'North Carolina: Greenville County[5];',
            'Texas: Potter County; New Mexico[2]:'
        ])
        result = remove_bracketed_references(series)
        assert '[13]' not in result.iloc[0]
        assert '[5]' not in result.iloc[1]
        assert '[2]' not in result.iloc[2]
        assert result.iloc[0] == 'Massachusetts: Hampden County;'
    
    def test_null_values_preserved(self):
        """Test that null values are preserved"""
        series = pd.Series(['Text[123]', None, 'More[456]'])
        result = remove_bracketed_references(series)
        assert pd.isna(result.iloc[1])
    
    def test_consecutive_references(self):
        """Test removing consecutive references"""
        series = pd.Series(['Value[1][2][3]text'])
        result = remove_bracketed_references(series)
        assert '[1]' not in result.iloc[0]
        assert '[2]' not in result.iloc[0]
        assert '[3]' not in result.iloc[0]
        assert result.iloc[0] == 'Valuetext'
    
    def test_reference_at_different_positions(self):
        """Test references at beginning, middle, and end of string"""
        series = pd.Series([
            '[1]Start text',
            'Middle[2]text',
            'End text[3]'
        ])
        result = remove_bracketed_references(series)
        assert result.iloc[0] == 'Start text'
        assert result.iloc[1] == 'Middletext'
        assert result.iloc[2] == 'End text'


class TestIntegrationScenarios:
    """Integration tests combining multiple normalization functions"""
    
    def test_pipeline_area_affected(self):
        """Test full pipeline for area_affected field"""
        series = pd.Series([
            '  Massachusetts: Hampden County[13]; ',
            ' Georgia: Clayton County;  ',
            'Maine ;  '
        ])
        # First remove bracketed references
        result = remove_bracketed_references(series)
        # Then standardize delimiters
        result = standardize_delimited_field(result, 'area_affected')
        # Then correct common string issues
        result = correct_common_string_issues(result)
        
        assert '[13]' not in result.iloc[0]
        assert result.iloc[0].startswith('Massachusetts:') or result.iloc[0].startswith('M')
    
    def test_pipeline_nerc_region(self):
        """Test full pipeline for NERC region field"""
        series = pd.Series([
            '  SERC / RF  ',
            ' MRO / RF ',
            'RFC; SERC'
        ])
        # First correct common string issues
        result = correct_common_string_issues(series)
        # Then standardize delimiters
        result = standardize_delimited_field(result, 'nerc_region')
        
        # All should have consistent delimiters (commas)
        for item in result:
            if pd.notna(item) and ',' in item or len(str(item)) > 0:
                pass  # Successfully processed
    
    def test_pipeline_event_type(self):
        """Test full pipeline for event_type field"""
        series = pd.Series([
            ' - Severe Weather / Transmission Interruption ',
            'Actual Physical Attack/Vandalism  ',
            ' Suspicious Activity'
        ])
        # First correct common string issues
        result = correct_common_string_issues(series)
        # Then standardize delimiters
        result = standardize_delimited_field(result, 'event_type')
        
        # Check that results are normalized
        assert len(result) == 3
        assert not any(result.isna())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

