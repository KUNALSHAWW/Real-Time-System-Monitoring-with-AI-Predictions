"""
Anomaly Detection Engine
Uses Isolation Forest, Local Outlier Factor, and Autoencoders
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict, Any, List
import logging
from datetime import datetime
import joblib

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Multi-algorithm anomaly detection system
    """
    
    def __init__(
        self,
        algorithm: str = "isolation_forest",
        threshold: float = 0.7,
        contamination: float = 0.1
    ):
        self.algorithm = algorithm
        self.threshold = threshold
        self.contamination = contamination
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize anomaly detection model"""
        if self.algorithm == "isolation_forest":
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_jobs=-1
            )
        elif self.algorithm == "local_outlier_factor":
            self.model = LocalOutlierFactor(
                contamination=self.contamination,
                novelty=True,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")
    
    def fit(self, X: np.ndarray) -> 'AnomalyDetector':
        """Fit anomaly detector to historical data"""
        try:
            # Normalize data
            X_scaled = self.scaler.fit_transform(X)
            
            # Fit model
            self.model.fit(X_scaled)
            self.is_fitted = True
            
            logger.info(f"✅ {self.algorithm} model fitted on {X.shape[0]} samples")
            return self
        
        except Exception as e:
            logger.error(f"Error fitting model: {str(e)}")
            raise
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies
        
        Returns:
        - is_anomaly: Boolean array indicating anomalies
        - scores: Anomaly scores (0-1)
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        
        try:
            # Normalize data using fitted scaler
            X_scaled = self.scaler.transform(X)
            
            # Get predictions
            predictions = self.model.predict(X_scaled)
            
            # Get anomaly scores
            if hasattr(self.model, 'offset_'):
                # Isolation Forest
                scores = 1 / (1 + np.exp(-self.model.score_samples(X_scaled)))
            else:
                # Local Outlier Factor
                lof_scores = self.model.negative_outlier_factor_
                scores = 1 / (1 + np.exp(lof_scores))
            
            # Convert to binary
            is_anomaly = (scores > self.threshold).astype(int)
            
            return is_anomaly, scores
        
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise
    
    def predict_single(self, x: List[float]) -> Tuple[bool, float]:
        """Predict single data point"""
        X = np.array([x])
        is_anomaly, scores = self.predict(X)
        return bool(is_anomaly[0]), float(scores[0])
    
    def save(self, filepath: str):
        """Save model to disk"""
        try:
            joblib.dump({
                "model": self.model,
                "scaler": self.scaler,
                "algorithm": self.algorithm,
                "threshold": self.threshold,
                "contamination": self.contamination,
                "is_fitted": self.is_fitted
            }, filepath)
            logger.info(f"✅ Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load(self, filepath: str):
        """Load model from disk"""
        try:
            data = joblib.load(filepath)
            self.model = data["model"]
            self.scaler = data["scaler"]
            self.algorithm = data["algorithm"]
            self.threshold = data["threshold"]
            self.contamination = data["contamination"]
            self.is_fitted = data["is_fitted"]
            logger.info(f"✅ Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise


class TimeSeriesAnomalyDetector:
    """
    Time series specific anomaly detection
    Uses sliding window and statistical methods
    """
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.mean = None
        self.std = None
        self.is_fitted = False
    
    def fit(self, data: List[float]) -> 'TimeSeriesAnomalyDetector':
        """Fit on historical data"""
        self.mean = np.mean(data)
        self.std = np.std(data)
        self.is_fitted = True
        logger.info(f"✅ Time series detector fitted (mean={self.mean:.2f}, std={self.std:.2f})")
        return self
    
    def detect_zscore(self, value: float, threshold: float = 3.0) -> Tuple[bool, float]:
        """Detect anomaly using Z-score"""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted first")
        
        if self.std == 0:
            return False, 0.0
        
        z_score = abs((value - self.mean) / self.std)
        is_anomaly = z_score > threshold
        
        return is_anomaly, min(z_score / threshold, 1.0)
    
    def detect_iqr(self, data: List[float], k: float = 1.5) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies using Interquartile Range"""
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        is_anomaly = (np.array(data) < lower_bound) | (np.array(data) > upper_bound)
        
        # Calculate anomaly scores
        scores = np.zeros(len(data))
        for i, val in enumerate(data):
            if is_anomaly[i]:
                if val < lower_bound:
                    scores[i] = (lower_bound - val) / IQR if IQR > 0 else 1.0
                else:
                    scores[i] = (val - upper_bound) / IQR if IQR > 0 else 1.0
        
        return is_anomaly, scores


# Global detector instances
_detector: Dict[str, AnomalyDetector] = {}
_ts_detector: Dict[str, TimeSeriesAnomalyDetector] = {}


def get_anomaly_detector(metric_name: str, algorithm: str = "isolation_forest") -> AnomalyDetector:
    """Get or create anomaly detector for metric"""
    key = f"{metric_name}_{algorithm}"
    
    if key not in _detector:
        _detector[key] = AnomalyDetector(algorithm=algorithm)
    
    return _detector[key]


def get_ts_anomaly_detector(metric_name: str) -> TimeSeriesAnomalyDetector:
    """Get or create time series anomaly detector"""
    if metric_name not in _ts_detector:
        _ts_detector[metric_name] = TimeSeriesAnomalyDetector()
    
    return _ts_detector[metric_name]
