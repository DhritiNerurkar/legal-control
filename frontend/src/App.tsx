import React, { useState } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Button,
} from '@mui/material';
import {
  AccountBalance as AccountBalanceIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import DueDiligenceForm from './components/DueDiligenceForm';
import CheckResults from './components/CheckResults';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [currentCheckId, setCurrentCheckId] = useState<string | null>(null);

  const handleCheckSubmitted = (checkId: string) => {
    setCurrentCheckId(checkId);
  };

  const handleGoHome = () => {
    setCurrentCheckId(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <AccountBalanceIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Legal Entity Due Diligence System
          </Typography>
          {currentCheckId && (
            <Button
              color="inherit"
              startIcon={<HomeIcon />}
              onClick={handleGoHome}
            >
              New Check
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {currentCheckId ? (
          <CheckResults checkId={currentCheckId} />
        ) : (
          <Box>
            <Box textAlign="center" mb={4}>
              <Typography variant="h3" component="h1" gutterBottom>
                Legal Entity Due Diligence
              </Typography>
              <Typography variant="h6" color="text.secondary" paragraph>
                Automated 5-Point Legal Due Diligence Checks for Financial Entities
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Our AI-powered system performs comprehensive due diligence checks covering:
                Entity Classification, Jurisdiction Analysis, Authority Verification,
                Capacity Assessment, and Legal Opinion Review.
              </Typography>
            </Box>

            <DueDiligenceForm onSubmit={handleCheckSubmitted} />

            <Box mt={6} p={3} bgcolor="grey.50" borderRadius={2}>
              <Typography variant="h6" gutterBottom>
                About the 5-Point Check
              </Typography>
              <Box component="ol" sx={{ pl: 2 }}>
                <Box component="li" mb={1}>
                  <Typography variant="body2">
                    <strong>Entity Classification:</strong> Determines if the entity is a bank, hedge fund, asset manager, or other entity type
                  </Typography>
                </Box>
                <Box component="li" mb={1}>
                  <Typography variant="body2">
                    <strong>Jurisdiction:</strong> Identifies where the entity is incorporated and the applicable governing law
                  </Typography>
                </Box>
                <Box component="li" mb={1}>
                  <Typography variant="body2">
                    <strong>Authority:</strong> Verifies the entity has the authority to enter into the specified derivative contracts
                  </Typography>
                </Box>
                <Box component="li" mb={1}>
                  <Typography variant="body2">
                    <strong>Capacity:</strong> Confirms the entity has the legal capacity to enter into the specified products
                  </Typography>
                </Box>
                <Box component="li" mb={1}>
                  <Typography variant="body2">
                    <strong>Legal Opinion:</strong> Checks for legal opinion coverage ensuring enforceability of contract and close-out netting rights
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        )}
      </Container>
    </ThemeProvider>
  );
}

export default App;