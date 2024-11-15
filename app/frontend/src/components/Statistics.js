import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Grid,
  Paper,
  Alert
} from '@mui/material';
import axios from 'axios';

export default function Statistics() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('/api/stats');
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setError('Failed to load statistics. Please try again later.');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!stats) {
    return (
      <Typography color="textSecondary">
        No statistics available yet.
      </Typography>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Overall Performance
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Paper elevation={0} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {stats.total_correct || 0}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Correct Picks
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper elevation={0} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {stats.accuracy ? `${stats.accuracy.toFixed(1)}%` : '0%'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Accuracy
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Highlights
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Paper elevation={0} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {stats.best_week?.correct || 0}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Best Week (Week {stats.best_week?.week || '-'})
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper elevation={0} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {stats.current_streak || 0}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Current Streak
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Weekly Performance
              </Typography>
              <Grid container spacing={2}>
                {stats.weekly_stats?.map((week) => (
                  <Grid item xs={12} sm={6} md={4} key={week.week}>
                    <Paper elevation={0} sx={{ p: 2 }}>
                      <Typography variant="subtitle1">
                        Week {week.week}
                      </Typography>
                      <Typography>
                        {week.correct}/{week.total} ({(week.accuracy || 0).toFixed(1)}%)
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
