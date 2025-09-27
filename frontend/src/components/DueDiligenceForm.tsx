import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  SelectChangeEvent,
  Alert,
  CircularProgress,
  Autocomplete,
} from '@mui/material';
import { ProductType, DueDiligenceRequest } from '../types/api';
import { dueDiligenceApi } from '../services/api';

interface DueDiligenceFormProps {
  onSubmit: (checkId: string) => void;
}

const PRODUCT_OPTIONS = Object.values(ProductType);

// Known entities for easy selection
const KNOWN_ENTITIES = [
  {
    legal_name: "Goldman Sachs Asset Management LLC",
    lei_number: "LMPQFR1LHAW71HGQGA77",
    type: "Asset Manager"
  },
  {
    legal_name: "Bridgewater Associates LP",
    lei_number: "5493006MHB84DD0ZWV18",
    type: "Hedge Fund"
  },
  {
    legal_name: "JPMorgan Chase Bank, National Association",
    lei_number: "7H6GLXDRUGQFU57RNE97",
    type: "Commercial Bank"
  },
  {
    legal_name: "Man Group plc",
    lei_number: "MLKBWG1CBLZLWR7DYP07",
    type: "Asset Manager"
  },
  {
    legal_name: "Two Sigma Investments, LP",
    lei_number: "549300DHLU1APW6NMU86",
    type: "Hedge Fund"
  }
];

const DueDiligenceForm: React.FC<DueDiligenceFormProps> = ({ onSubmit }) => {
  const [formData, setFormData] = useState<DueDiligenceRequest>({
    legal_name: '',
    lei_number: '',
    products: [],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<typeof KNOWN_ENTITIES[0] | null>(null);

  const handleInputChange = (field: keyof DueDiligenceRequest) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const newValue = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: newValue,
    }));
    setError(null);

    // Clear selected entity when user manually edits fields that don't match the selected entity
    if (selectedEntity) {
      if (field === 'legal_name' && newValue !== selectedEntity.legal_name) {
        setSelectedEntity(null);
      } else if (field === 'lei_number' && newValue !== selectedEntity.lei_number) {
        setSelectedEntity(null);
      }
    }
  };

  const handleProductsChange = (event: SelectChangeEvent<ProductType[]>) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      products: typeof value === 'string' ? [] : value,
    }));
    setError(null);
  };

  const handleEntitySelection = (entity: typeof KNOWN_ENTITIES[0] | null) => {
    setSelectedEntity(entity);
    if (entity) {
      setFormData(prev => ({
        ...prev,
        legal_name: entity.legal_name,
        lei_number: entity.lei_number,
      }));
    }
    setError(null);
  };

  const validateForm = (): string | null => {
    if (!formData.legal_name.trim()) {
      return 'Legal name is required';
    }
    if (!formData.lei_number.trim()) {
      return 'LEI number is required';
    }
    if (formData.lei_number.length !== 20) {
      return 'LEI number must be exactly 20 characters';
    }
    if (!/^[A-Z0-9]{20}$/.test(formData.lei_number)) {
      return 'LEI number must contain only uppercase letters and numbers';
    }
    if (formData.products.length === 0) {
      return 'At least one product must be selected';
    }
    return null;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await dueDiligenceApi.createCheck(formData);
      onSubmit(response.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create due diligence check');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Legal Entity Due Diligence Check
      </Typography>

      <Typography variant="body2" color="text.secondary" paragraph>
        Enter the entity details below to initiate a comprehensive 5-point due diligence check.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
          Select Known Entity or Enter New Entity:
        </Typography>

        <Autocomplete
          fullWidth
          options={KNOWN_ENTITIES}
          getOptionLabel={(option) => `${option.legal_name} (${option.type})`}
          value={selectedEntity}
          onChange={(event, newValue) => handleEntitySelection(newValue)}
          clearOnEscape
          clearOnBlur
          renderInput={(params) => (
            <TextField
              {...params}
              label="Select Known Entity"
              placeholder="Choose from known entities or leave empty to enter new"
              variant="outlined"
              margin="normal"
            />
          )}
          renderOption={(props, option) => (
            <Box component="li" {...props}>
              <Box>
                <Typography variant="body1">{option.legal_name}</Typography>
                <Typography variant="caption" color="textSecondary">
                  LEI: {option.lei_number} | Type: {option.type}
                </Typography>
              </Box>
            </Box>
          )}
        />

        <TextField
          fullWidth
          label="Legal Name"
          value={formData.legal_name}
          onChange={handleInputChange('legal_name')}
          margin="normal"
          required
          placeholder="e.g., Goldman Sachs Asset Management LLC"
          helperText={selectedEntity ? "Edit as needed or clear selection above to start fresh" : "Enter manually or select from known entities above"}
        />

        <TextField
          fullWidth
          label="LEI Number"
          value={formData.lei_number}
          onChange={handleInputChange('lei_number')}
          margin="normal"
          required
          placeholder="e.g., LMPQFR1LHAW71HGQGA77"
          inputProps={{ maxLength: 20 }}
          helperText={selectedEntity ? "Edit as needed or clear selection above to start fresh" : "20-character alphanumeric identifier"}
        />

        <FormControl fullWidth margin="normal" required>
          <InputLabel>Products</InputLabel>
          <Select
            multiple
            value={formData.products}
            onChange={handleProductsChange}
            input={<OutlinedInput label="Products" />}
            MenuProps={{
              PaperProps: {
                style: {
                  maxHeight: 224,
                  width: 250,
                },
              },
            }}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {PRODUCT_OPTIONS.map((product) => (
              <MenuItem key={product} value={product}>
                {product}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Starting Check...' : 'Start Due Diligence Check'}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default DueDiligenceForm;