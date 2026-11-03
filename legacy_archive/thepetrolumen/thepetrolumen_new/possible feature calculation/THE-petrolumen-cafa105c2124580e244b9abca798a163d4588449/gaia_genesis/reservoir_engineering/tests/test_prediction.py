import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from ..prediction.ai_prediction import AIPrediction
from ..decline_analysis.advanced_decline import AdvancedDeclineAnalysis

@pytest.fixture
def sample_data():
    """Fixture com dados de exemplo."""
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    oil_rates = np.random.normal(1000, 100, 100)
    gas_rates = oil_rates * np.random.uniform(0.8, 1.2, 100)
    water_rates = oil_rates * np.random.uniform(0.1, 0.3, 100)
    pressures = np.random.normal(2000, 100, 100)
    
    return pd.DataFrame({
        'date': dates,
        'q_oleo': oil_rates,
        'q_gas': gas_rates,
        'q_agua': water_rates,
        'pressao': pressures
    })

@pytest.fixture
def ai_predictor():
    """Fixture com instância do preditor."""
    return AIPrediction()

@pytest.fixture
def decline_analyzer():
    """Fixture com instância do analisador de declínio."""
    return AdvancedDeclineAnalysis()

def test_data_preparation(ai_predictor, sample_data):
    """Testa preparação de dados."""
    X_train, X_test, y_train, y_test = ai_predictor.prepare_data(
        data=sample_data,
        target_column='q_oleo',
        feature_columns=['q_gas', 'q_agua', 'pressao'],
        test_size=0.2
    )
    
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20

def test_model_training(ai_predictor, sample_data):
    """Testa treinamento de modelos."""
    X_train, X_test, y_train, y_test = ai_predictor.prepare_data(
        data=sample_data,
        target_column='q_oleo',
        feature_columns=['q_gas', 'q_agua', 'pressao']
    )
    
    ai_predictor.train_models(X_train, y_train, X_test, y_test)
    
    assert 'svr' in ai_predictor.models
    assert 'xgb' in ai_predictor.models
    assert ai_predictor.best_model is not None

def test_prediction(ai_predictor, sample_data):
    """Testa previsões."""
    X_train, X_test, y_train, y_test = ai_predictor.prepare_data(
        data=sample_data,
        target_column='q_oleo',
        feature_columns=['q_gas', 'q_agua', 'pressao']
    )
    
    ai_predictor.train_models(X_train, y_train, X_test, y_test)
    predictions = ai_predictor.predict(X_test)
    
    assert len(predictions) == len(y_test)
    assert not np.any(np.isnan(predictions))

def test_feature_importance(ai_predictor, sample_data):
    """Testa cálculo de importância das features."""
    X_train, X_test, y_train, y_test = ai_predictor.prepare_data(
        data=sample_data,
        target_column='q_oleo',
        feature_columns=['q_gas', 'q_agua', 'pressao']
    )
    
    ai_predictor.train_models(X_train, y_train, X_test, y_test)
    
    assert ai_predictor.feature_importance is not None
    assert len(ai_predictor.feature_importance) == 3

def test_model_saving_loading(ai_predictor, sample_data, tmp_path):
    """Testa salvamento e carregamento de modelo."""
    X_train, X_test, y_train, y_test = ai_predictor.prepare_data(
        data=sample_data,
        target_column='q_oleo',
        feature_columns=['q_gas', 'q_agua', 'pressao']
    )
    
    ai_predictor.train_models(X_train, y_train, X_test, y_test)
    
    # Salva modelo
    model_path = tmp_path / "model.joblib"
    ai_predictor.save_model(str(model_path))
    
    # Carrega modelo
    new_predictor = AIPrediction()
    new_predictor.load_model(str(model_path))
    
    # Compara previsões
    original_pred = ai_predictor.predict(X_test)
    loaded_pred = new_predictor.predict(X_test)
    
    np.testing.assert_array_almost_equal(original_pred, loaded_pred)

def test_decline_analysis(decline_analyzer, sample_data):
    """Testa análise de declínio."""
    time = np.arange(len(sample_data))
    rate = sample_data['q_oleo'].values
    
    models = decline_analyzer.fit_models(time, rate)
    
    assert 'exponential' in models
    assert 'hyperbolic' in models
    assert 'harmonic' in models
    assert decline_analyzer.best_model is not None

def test_decline_prediction(decline_analyzer, sample_data):
    """Testa previsão de declínio."""
    time = np.arange(len(sample_data))
    rate = sample_data['q_oleo'].values
    
    decline_analyzer.fit_models(time, rate)
    future = decline_analyzer.predict_future(months=12)
    
    assert 'time' in future
    assert 'rate' in future
    assert len(future['time']) == 12
    assert len(future['rate']) == 12

def test_decline_plotting(decline_analyzer, sample_data, tmp_path):
    """Testa geração de gráficos."""
    time = np.arange(len(sample_data))
    rate = sample_data['q_oleo'].values
    
    decline_analyzer.fit_models(time, rate)
    
    # Testa plotagem
    fig = decline_analyzer.plot_decline_curves(time, rate)
    assert fig is not None
    
    # Testa salvamento
    save_path = tmp_path / "decline_plot.png"
    fig = decline_analyzer.plot_decline_curves(time, rate, str(save_path))
    assert save_path.exists()

def test_decline_report(decline_analyzer, sample_data, tmp_path):
    """Testa geração de relatório."""
    time = np.arange(len(sample_data))
    rate = sample_data['q_oleo'].values
    
    decline_analyzer.fit_models(time, rate)
    
    # Testa geração de relatório
    report_path = tmp_path / "report.pdf"
    decline_analyzer.generate_report("P1", str(report_path))
    assert report_path.exists()
    
    # Testa exportação para Excel
    excel_path = tmp_path / "results.xlsx"
    decline_analyzer.export_to_excel("P1", str(excel_path))
    assert excel_path.exists() 