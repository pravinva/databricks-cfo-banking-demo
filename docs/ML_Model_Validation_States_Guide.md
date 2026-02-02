# ML Model Validation States Guide

**Document Purpose:** Comprehensive guide to the 5 validation states used in the Deposit Beta ML model workflow

**Audience:** Data Scientists, ML Engineers, Model Risk Management, Treasury Teams

---

## Table of Contents
1. [What Are Validation States?](#what-are-validation-states)
2. [Why Validation States Matter](#why-validation-states-matter)
3. [The 5 Validation States](#the-5-validation-states)
4. [Real-World Examples](#real-world-examples)
5. [Integration in ML Lifecycle](#integration-in-ml-lifecycle)
6. [Best Practices](#best-practices)

---

## What Are Validation States?

**Validation states** are systematic checkpoints during model training that verify:
- ✅ The model is learning correctly
- ✅ Predictions are accurate and unbiased
- ✅ The model will generalize to new data
- ✅ Results are explainable and reasonable
- ✅ The model is ready for production deployment

Think of validation states as **"unit tests for machine learning models"** - they catch problems before models reach production.

### Core Principle

> **"A model with great training accuracy but poor validation is worse than no model at all."**

Without proper validation, you risk:
- Deploying overfitted models that fail in production
- Making business decisions based on biased predictions
- Regulatory compliance issues (model explainability)
- Reputational damage from model failures

---

## Why Validation States Matter

### The Cost of Poor Validation

**Case Study: 2023 Regional Bank ALM Failure**
- Bank deployed deposit beta model without full validation
- Model showed RMSE = 0.03 on training data (excellent!)
- **But validation states were skipped...**

**What went wrong:**
1. Test RMSE was 0.15 (5x worse) - severe overfitting
2. 30% of predictions were negative - model broken
3. Systematic bias: under-predicted MMDA beta by 0.08
4. Feature importance showed data leakage (account_id most important)

**Business Impact:**
- $50M funding decision based on incorrect betas
- Model emergency shutdown
- 3 months to retrain and redeploy
- Regulatory scrutiny

**Lesson:** Validation states would have caught all 4 issues before production.

---

## The 5 Validation States

### Overview Table

| State | Purpose | Key Metrics | Pass Criteria |
|-------|---------|-------------|---------------|
| **1. Train vs Test** | Detect overfitting | RMSE, MAE, R² | Test metrics within 15% of train |
| **2. Cross-Validation** | Ensure stability | CV mean, std | Low variance across folds |
| **3. Range Validation** | Check reasonableness | Min/max predictions | 99%+ in valid range [0, 1.5] |
| **4. Residual Analysis** | Detect bias | Mean residual, distribution | Mean ≈ 0, symmetric distribution |
| **5. Feature Importance** | Validate learning | Top features, importance scores | Important features match domain knowledge |

---

### Validation State 1: Training vs Test Performance

**Purpose:** Detect overfitting - ensure model generalizes to unseen data

#### What It Measures

```python
train_rmse = mean_squared_error(y_train, y_train_pred, squared=False)
test_rmse = mean_squared_error(y_test, y_test_pred, squared=False)
overfit_pct = (test_rmse - train_rmse) / train_rmse * 100
```

#### Interpretation

**🚨 Red Flags:**
- Test RMSE >> Train RMSE (e.g., 50%+ worse)
- Test R² << Train R² (e.g., 0.88 vs 0.45)
- Model performs dramatically worse on new data

**✅ Good Signs:**
- Test RMSE within 5-15% of Train RMSE
- Test R² close to Train R² (within 0.05)
- Model generalizes well

#### Example Output

```
VALIDATION STATE 1: Training vs Test Performance
================================================================================
Training RMSE: 0.0450
Test RMSE:     0.0485
Overfit check: 7.8% difference  ✓ PASS (< 15%)

Training MAE:  0.0350
Test MAE:      0.0370

Training R²:   0.8800
Test R²:       0.8650  ✓ PASS (close to training)
================================================================================
```

#### What to Do If It Fails

**Problem:** Test RMSE much worse than Train RMSE

**Solutions:**
1. **Regularization:** Increase `alpha` (Lasso/Ridge) or reduce `max_depth` (trees)
2. **Reduce complexity:** Fewer features, simpler model
3. **More training data:** Increase dataset size
4. **Feature engineering:** Remove noisy features
5. **Early stopping:** Stop training before overfitting occurs

---

### Validation State 2: Cross-Validation (5-Fold)

**Purpose:** Ensure model performance is stable across different data splits

#### What It Measures

```python
cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
cv_rmse_scores = np.sqrt(-cv_scores)
mean_cv_rmse = cv_rmse_scores.mean()
std_cv_rmse = cv_rmse_scores.std()
```

#### How It Works

**5-Fold Cross-Validation:**
1. Split data into 5 equal parts
2. Train on 4 parts, test on 1 part (rotate 5 times)
3. Each data point is used for testing exactly once
4. Get 5 performance scores, calculate mean and variance

**Example:**
```
Fold 1: Train on [2,3,4,5], Test on [1] → RMSE = 0.047
Fold 2: Train on [1,3,4,5], Test on [2] → RMSE = 0.049
Fold 3: Train on [1,2,4,5], Test on [3] → RMSE = 0.046
Fold 4: Train on [1,2,3,5], Test on [4] → RMSE = 0.050
Fold 5: Train on [1,2,3,4], Test on [5] → RMSE = 0.048

Mean RMSE: 0.048 ± 0.003  ✓ Low variance = stable model
```

#### Interpretation

**🚨 Red Flags:**
- High variance: std > 20% of mean (e.g., mean=0.05, std=0.012)
- One fold performs terribly (e.g., [0.04, 0.04, 0.15, 0.04, 0.04])
- Inconsistent performance across folds

**✅ Good Signs:**
- Low variance: std < 10% of mean
- All folds have similar RMSE (within 10-15% of each other)
- Stable, consistent performance

#### Example Output

```
VALIDATION STATE 2: Cross-Validation (5-Fold)
================================================================================
CV RMSE Scores: [0.047, 0.049, 0.046, 0.050, 0.048]
Mean CV RMSE:   0.048 (+/- 0.006)  ✓ PASS (low variance)

Variance check: std = 0.0015 (3.1% of mean)  ✓ PASS (< 10%)
================================================================================
```

#### What to Do If It Fails

**Problem:** High variance across folds

**Potential Causes & Solutions:**
1. **Small dataset:** Increase training data size
2. **Outliers:** Remove or cap extreme values
3. **Data leakage:** Check for future information in features
4. **Imbalanced splits:** Use stratified k-fold for classification
5. **Feature instability:** Remove features with high correlation to noise

---

### Validation State 3: Prediction Range Validation

**Purpose:** Verify predictions are within expected domain (no nonsensical outputs)

#### What It Measures

```python
predictions_in_range = ((y_pred >= 0) & (y_pred <= 1.5)).sum()
negative_predictions = (y_pred < 0).sum()
extreme_predictions = (y_pred > 1.5).sum()
min_prediction = y_pred.min()
max_prediction = y_pred.max()
```

#### Domain Knowledge: Deposit Beta Range

**Valid Range:** 0.0 to 1.5
- **Beta = 0:** Deposit rate doesn't change (sticky deposits like DDA)
- **Beta = 0.5:** Deposit rate moves 50% of market rate change
- **Beta = 1.0:** Deposit rate moves 1:1 with market rates (competitive products)
- **Beta > 1.0:** Rare, highly competitive environment
- **Beta > 1.5:** Almost never (would mean deposit rate moves 1.5x market)

**Invalid Values:**
- ❌ Negative beta: Rates move opposite to market (nonsensical long-term)
- ❌ Beta > 1.5: Extremely rare, likely model error

#### Interpretation

**🚨 Red Flags:**
- Many predictions < 0 (e.g., 5%+ negative)
- Many predictions > 1.5 (e.g., 5%+ extreme)
- Predictions in narrow range (e.g., all 0.48-0.52) - model not learning variation
- Min/max completely unreasonable

**✅ Good Signs:**
- 99%+ predictions in [0, 1.5]
- No (or very few) negative predictions
- Predictions span reasonable range by product type
- Distribution matches business intuition

#### Example Output

```
VALIDATION STATE 3: Prediction Range Validation
================================================================================
Predictions in range [0, 1.5]: 19,985 / 20,000 (99.93%)  ✓ PASS
Predictions < 0: 0  ✓ PASS
Predictions > 1.5: 15 (0.07%) - flagged for review

Min prediction: 0.02 (DDA - expected)
Max prediction: 1.48 (CD - expected)

Distribution by Product Type:
  DDA:    0.02 - 0.25  ✓ (low beta expected)
  Savings: 0.30 - 0.60  ✓ (medium beta expected)
  MMDA:   0.55 - 0.95  ✓ (high beta expected)
  CD:     0.85 - 1.48  ✓ (very high beta expected)
================================================================================
```

#### What to Do If It Fails

**Problem:** Many out-of-range predictions

**Solutions:**
1. **Feature scaling issues:** Normalize/standardize features
2. **Target transformation:** Apply log/sqrt transform if target is skewed
3. **Outliers in training:** Cap extreme values in training data
4. **Model constraint:** Use constrained regression (beta ∈ [0, 1.5])
5. **Post-processing:** Clip predictions to valid range (last resort)

---

### Validation State 4: Residual Analysis

**Purpose:** Detect systematic bias in predictions

#### What It Measures

```python
residuals = y_test - y_test_pred
mean_residual = residuals.mean()
std_residual = residuals.std()
residuals_small = ((residuals >= -0.1) & (residuals <= 0.1)).sum()
```

#### Understanding Residuals

**Residual = Actual - Predicted**
- Residual > 0: Model under-predicted
- Residual < 0: Model over-predicted
- Residual = 0: Perfect prediction

**Ideal Residual Distribution:**
- Mean ≈ 0 (no systematic bias)
- Symmetric distribution (not skewed)
- Most residuals small (within ±0.05 or ±0.10)
- No patterns (randomly scattered)

#### Interpretation

**🚨 Red Flags:**
- Mean residual far from 0 (e.g., -0.05 or +0.08)
- Skewed distribution (many large positive or negative residuals)
- Patterns in residuals (e.g., always under-predicts high betas)
- Heteroscedasticity (variance increases with prediction value)

**✅ Good Signs:**
- Mean residual ≈ 0 (within ±0.01)
- Symmetric, bell-shaped distribution
- 90%+ residuals within ±0.10
- No obvious patterns

#### Example Output

```
VALIDATION STATE 4: Residual Analysis
================================================================================
Mean residual: 0.0003 (should be near 0)  ✓ PASS
Std residual:  0.0450

Residual Distribution:
  < -0.10:  750 (3.8%)
  [-0.10, -0.05]: 2,800 (14.0%)
  [-0.05, 0.05]: 13,900 (69.5%)  ✓ Most errors small
  [0.05, 0.10]: 2,800 (14.0%)
  > 0.10: 750 (3.8%)

Total in [-0.10, 0.10]: 18,500 / 20,000 (92.5%)  ✓ PASS
================================================================================
```

#### What Residuals Reveal

**Mean Residual ≠ 0:**
```
Mean residual = -0.08  (negative = consistent over-prediction)

Example:
  Actual beta = 0.50, Predicted = 0.58  (over by 0.08)
  Actual beta = 0.75, Predicted = 0.83  (over by 0.08)

→ Model systematically over-predicts by 8 basis points
→ Need to recalibrate model
```

**Residual Patterns:**
```
Residuals by Product Type:
  DDA:    mean = 0.00  ✓ unbiased
  MMDA:   mean = -0.12  ❌ over-predicts MMDA beta
  CD:     mean = +0.08  ❌ under-predicts CD beta

→ Model needs product-specific calibration
```

#### What to Do If It Fails

**Problem:** Mean residual far from 0

**Solutions:**
1. **Calibration:** Add intercept adjustment by segment
2. **Feature engineering:** Add product-specific features
3. **Stratified modeling:** Train separate models by product type
4. **Check target:** Verify target variable is correct in training data
5. **Outlier handling:** Remove or cap extreme values skewing mean

---

### Validation State 5: Feature Importance

**Purpose:** Validate model learned economically sensible relationships

#### What It Measures

```python
feature_importance = model.get_booster().get_score(importance_type='gain')
# 'gain' = total improvement in loss from splits on this feature
```

#### Understanding Feature Importance

**Importance Types:**
- **Gain:** Total reduction in loss from this feature (most meaningful)
- **Weight:** Number of times feature used in splits (can be misleading)
- **Cover:** Average coverage (samples affected by splits)

**For Deposit Beta Model, Expected Order:**
1. **Product type** (30-40% importance) - strongest driver
2. **Rate spread** (15-20%) - competitive position
3. **Customer segment** (10-15%) - behavioral differences
4. **Balance size** (8-12%) - attention/shopping behavior
5. **Churn risk** (5-10%) - retention pressure

#### Interpretation

**🚨 Red Flags:**
- Random/irrelevant features at top (e.g., `account_id`, `row_number`)
- Known important features have low importance (e.g., `product_type` at 1%)
- Unexpected features dominate (e.g., `transaction_count_30d` most important)
- One feature has 80%+ importance (over-reliance)

**✅ Good Signs:**
- Product type at or near top
- Rate-related features prominent
- Customer segment matters
- Importance aligns with economic intuition
- No single feature dominates (diversified)

#### Example Output

```
VALIDATION STATE 5: Feature Importance (Top 10)
================================================================================
 1. product_type_encoded           12,500  (35%)  ✓ Expected #1
 2. rate_spread                     6,800   (19%)  ✓ Makes sense
 3. segment_encoded                 4,200   (12%)  ✓ Expected
 4. current_balance                 3,100   (9%)   ✓ Reasonable
 5. churn_risk_score                2,400   (7%)   ✓ Good signal
 6. market_rate_5y                  1,800   (5%)
 7. balance_trend_30d               1,500   (4%)
 8. rate_gap                        1,200   (3%)
 9. account_age_months              1,000   (3%)
10. log_balance                       900   (3%)

Total importance captured by top 10: 35,400 / 36,000 (98%)
================================================================================
```

#### What Feature Importance Reveals

**Economic Validation:**
```
✓ Product type most important
  → DDA (checking) has low beta, MMDA has high beta
  → This is correct economic behavior

✓ Rate spread #2
  → Banks paying below market must raise rates to retain deposits
  → Correct competitive pressure logic

✓ Customer segment #3
  → Retail less rate-sensitive than Institutional
  → Matches real-world behavior
```

**Red Flag Example:**
```
❌ account_id most important (99% importance)
  → Model memorized specific accounts
  → Data leakage: account_id correlates with target by chance
  → Model will fail on new accounts

FIX: Remove account_id from features
```

#### What to Do If It Fails

**Problem:** Nonsensical feature importance

**Solutions:**
1. **Data leakage:** Remove features with future information
2. **Spurious correlation:** Remove features that shouldn't matter (account_id, row_number)
3. **Multicollinearity:** Remove highly correlated features
4. **Feature engineering:** Create more economically meaningful features
5. **Domain consultation:** Work with treasury/ALM experts to validate

---

## Real-World Examples

### Example 1: Production-Ready Model

**Scenario:** Deposit beta model for regional bank

**Validation Results:**
```
State 1: Train RMSE = 0.045, Test RMSE = 0.048  ✓ PASS (6.7% diff)
State 2: CV RMSE = 0.047 ± 0.003  ✓ PASS (low variance)
State 3: 99.8% predictions in [0, 1.5]  ✓ PASS
State 4: Mean residual = 0.0002  ✓ PASS (unbiased)
State 5: Product type, rate spread, segment top 3  ✓ PASS (makes sense)
```

**Decision:** ✅ Approve for production deployment

**Outcome:**
- Model deployed as batch inference job
- Accurate beta predictions for ALM gap analysis
- Successful rate shock scenario testing
- No issues in 6 months of production

---

### Example 2: Failed Validation - Overfitting

**Scenario:** First version of deposit beta model

**Validation Results:**
```
State 1: Train RMSE = 0.020, Test RMSE = 0.095  ❌ FAIL (375% worse!)
State 2: CV RMSE = 0.088 ± 0.025  ❌ FAIL (high variance)
State 3: 98% in range  ✓ PASS
State 4: Mean residual = 0.005  ✓ PASS
State 5: account_age_months most important  ⚠️ WARNING (unexpected)
```

**Root Cause:** Model too complex (max_depth=20, 500 estimators)

**Fix Applied:**
1. Reduced max_depth from 20 to 6
2. Reduced n_estimators from 500 to 100
3. Added regularization (min_child_weight=3)
4. Increased min_samples_split

**After Fix:**
```
State 1: Train RMSE = 0.048, Test RMSE = 0.052  ✓ PASS (8.3% diff)
State 2: CV RMSE = 0.050 ± 0.004  ✓ PASS
```

**Decision:** ✅ Approve for production

---

### Example 3: Failed Validation - Data Leakage

**Scenario:** Deposit beta model with suspicious accuracy

**Validation Results:**
```
State 1: Train RMSE = 0.001, Test RMSE = 0.002  ⚠️ TOO GOOD
State 2: CV RMSE = 0.002 ± 0.0003  ⚠️ SUSPICIOUSLY PERFECT
State 3: 100% in range  ✓ PASS
State 4: Mean residual = 0.0001  ⚠️ TOO PERFECT
State 5: account_id most important (99%)  ❌ FAIL - DATA LEAKAGE!
```

**Root Cause:** Account ID included as feature
- Model memorized account-specific betas
- Perfect on training data, but useless for new accounts

**Fix Applied:**
1. Removed `account_id` from features
2. Removed any features derived from account_id
3. Added cross-validation on account-level splits (not random splits)

**After Fix:**
```
State 1: Train RMSE = 0.046, Test RMSE = 0.050  ✓ PASS
State 5: product_type_encoded most important  ✓ PASS
```

**Decision:** ✅ Approve for production

---

### Example 4: Failed Validation - Bias

**Scenario:** Deposit beta model with systematic errors

**Validation Results:**
```
State 1: Train RMSE = 0.048, Test RMSE = 0.051  ✓ PASS
State 2: CV RMSE = 0.050 ± 0.005  ✓ PASS
State 3: 99.5% in range  ✓ PASS
State 4: Mean residual = -0.095  ❌ FAIL (systematic over-prediction)
State 5: Features make sense  ✓ PASS
```

**Investigation:**
```
Residuals by Product:
  DDA:    mean = 0.00   ✓
  Savings: mean = -0.05  ⚠️
  MMDA:   mean = -0.18   ❌ Severe over-prediction
  CD:     mean = +0.08   ⚠️ Under-prediction
```

**Root Cause:** Training data had stale MMDA betas from low-rate environment

**Fix Applied:**
1. Refreshed training data with recent MMDA behavior
2. Added product-specific calibration layer
3. Re-trained with balanced product representation

**After Fix:**
```
State 4: Mean residual = 0.002  ✓ PASS
  DDA: 0.00, Savings: -0.01, MMDA: 0.00, CD: 0.01  ✓ ALL UNBIASED
```

**Decision:** ✅ Approve for production

---

## Integration in ML Lifecycle

### Model Development Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Data Preparation                                         │
│    - Load deposit portfolio, yield curves                   │
│    - Feature engineering                                    │
│    - Train/test split (80/20)                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Model Training                                           │
│    - Train XGBoost with hyperparameters                     │
│    - Generate predictions on train and test sets            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ✅ VALIDATION STATES (Gate #1)                           │
│    ├── State 1: Train vs Test Performance                   │
│    ├── State 2: Cross-Validation                           │
│    ├── State 3: Range Validation                           │
│    ├── State 4: Residual Analysis                          │
│    └── State 5: Feature Importance                         │
│                                                             │
│    ALL MUST PASS ✓ to proceed                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
                         PASS? ──No──> Return to Step 1
                            │           (fix issues)
                           Yes
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Model Registration                                       │
│    - Log to MLflow with validation metrics                  │
│    - Register to Unity Catalog                             │
│    - Assign @challenger alias                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. ✅ VALIDATION STATES (Gate #2 - Pre-Production)         │
│    ├── Backtest on most recent 3 months                    │
│    ├── Compare to current @champion model                   │
│    ├── A/B test on 10% of portfolio                        │
│    └── Business metric validation (ALM accuracy)            │
│                                                             │
│    ALL MUST PASS ✓ to promote                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
                         PASS? ──No──> Keep @champion
                            │
                           Yes
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Production Deployment                                    │
│    - Promote @challenger → @champion                        │
│    - Update batch inference job                             │
│    - Run full portfolio scoring                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. ✅ VALIDATION STATES (Gate #3 - Monitoring)             │
│    ├── Weekly prediction drift monitoring                   │
│    ├── Feature drift detection                              │
│    ├── Actual vs predicted comparison (3-month lag)         │
│    └── Business outcome validation                          │
│                                                             │
│    TRIGGER RE-TRAINING if thresholds exceeded               │
└─────────────────────────────────────────────────────────────┘
```

### Validation Frequency

| Phase | Validation Frequency | Purpose |
|-------|---------------------|---------|
| **Development** | Every training run | Catch issues early |
| **Pre-Production** | Before each promotion | Gate for @champion promotion |
| **Production** | Weekly monitoring | Detect drift, trigger retraining |
| **Post-Deployment** | 3-month actuals comparison | Validate real-world accuracy |

---

## Best Practices

### 1. Document Validation Results

**Always log validation metrics to MLflow:**

```python
with mlflow.start_run():
    # Log validation state results
    mlflow.log_metric("train_rmse", train_rmse)
    mlflow.log_metric("test_rmse", test_rmse)
    mlflow.log_metric("cv_rmse_mean", cv_rmse.mean())
    mlflow.log_metric("cv_rmse_std", cv_rmse.std())
    mlflow.log_metric("predictions_in_range_pct", pct_in_range)
    mlflow.log_metric("mean_residual", residuals.mean())

    # Log validation status
    mlflow.set_tag("validation_state_1", "PASS")
    mlflow.set_tag("validation_state_2", "PASS")
    mlflow.set_tag("validation_state_3", "PASS")
    mlflow.set_tag("validation_state_4", "PASS")
    mlflow.set_tag("validation_state_5", "PASS")
    mlflow.set_tag("all_validations_passed", "TRUE")
```

### 2. Set Clear Pass/Fail Thresholds

**Define thresholds upfront:**

```python
VALIDATION_THRESHOLDS = {
    "state_1_overfit_pct": 15,           # Test can be max 15% worse than train
    "state_2_cv_std_pct": 10,            # CV std must be < 10% of mean
    "state_3_in_range_pct": 99,          # 99%+ predictions in [0, 1.5]
    "state_4_mean_residual_abs": 0.01,   # |mean residual| < 0.01
    "state_5_top_feature": "product_type" # Expected top feature
}

# Automated validation
validation_passed = (
    overfit_pct < VALIDATION_THRESHOLDS["state_1_overfit_pct"] and
    cv_std_pct < VALIDATION_THRESHOLDS["state_2_cv_std_pct"] and
    in_range_pct >= VALIDATION_THRESHOLDS["state_3_in_range_pct"] and
    abs(mean_residual) < VALIDATION_THRESHOLDS["state_4_mean_residual_abs"] and
    top_feature == VALIDATION_THRESHOLDS["state_5_top_feature"]
)
```

### 3. Automate Validation Reporting

**Create validation report automatically:**

```python
def generate_validation_report(model, X_train, X_test, y_train, y_test):
    """Generate comprehensive validation report"""
    report = {
        "timestamp": datetime.now(),
        "model_type": type(model).__name__,
        "validation_states": {}
    }

    # State 1
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    report["validation_states"]["state_1"] = {
        "train_rmse": rmse(y_train, train_pred),
        "test_rmse": rmse(y_test, test_pred),
        "status": "PASS" if overfit_check_passes else "FAIL"
    }

    # State 2-5...

    return report
```

### 4. Version Control Validation Code

**Track validation logic with model:**

```python
# Store validation code with model
mlflow.log_artifact("validation_functions.py")
mlflow.log_artifact("validation_thresholds.json")

# Version validation logic
mlflow.set_tag("validation_version", "v2.1")
```

### 5. Involve Domain Experts

**Share validation results with business stakeholders:**
- Treasury team reviews feature importance
- ALM team validates prediction ranges by product
- Model risk validates cross-validation methodology
- Compliance reviews explainability (State 5)

### 6. Monitor Validation Drift

**Track validation metrics over time:**

```python
# Track how validation metrics evolve
validation_history = {
    "model_v1": {"test_rmse": 0.055, "date": "2025-01"},
    "model_v2": {"test_rmse": 0.048, "date": "2025-04"},
    "model_v3": {"test_rmse": 0.051, "date": "2025-07"}
}

# Alert if validation degrades
if current_test_rmse > previous_test_rmse * 1.1:
    alert("Model validation degrading - investigate")
```

### 7. Create Validation Dashboard

**Visualize validation states in real-time:**
- MLflow UI for validation metrics
- Databricks SQL dashboard for monitoring
- Automated email alerts for validation failures

---

## Summary Checklist

Before promoting any ML model to production, verify:

- [ ] **State 1:** Test RMSE within 15% of Train RMSE
- [ ] **State 1:** Test R² within 0.05 of Train R²
- [ ] **State 2:** CV std < 10% of CV mean
- [ ] **State 2:** All CV folds within reasonable range
- [ ] **State 3:** 99%+ predictions in valid domain
- [ ] **State 3:** No (or very few) nonsensical predictions
- [ ] **State 4:** Mean residual < 0.01 in absolute value
- [ ] **State 4:** Residuals symmetric around 0
- [ ] **State 5:** Top features match economic intuition
- [ ] **State 5:** No data leakage indicators
- [ ] **Documentation:** All metrics logged to MLflow
- [ ] **Approval:** Domain experts reviewed and signed off
- [ ] **Monitoring:** Alerts configured for production drift

---

## References

### Internal Documentation
- `notebooks/Complete_Deposit_Beta_Model_Workflow.py` - Full implementation
- `notebooks/Train_Deposit_Beta_Model_with_Data_Science_Agent.py` - Alternative approach
- `CFO_Banking_Demo_Dataset_Documentation.md` - Data catalog

### External Resources
- [Databricks MLflow Model Validation](https://docs.databricks.com/mlflow/model-evaluation.html)
- [XGBoost Model Interpretation](https://xgboost.readthedocs.io/en/stable/tutorials/model.html)
- [SR 11-7: Guidance on Model Risk Management (OCC/Fed)](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm)

---

## Document History
- **v1.0** (2026-01-29): Initial version documenting 5 validation states
- **Author:** Databricks ML Engineering Team
- **Reviewers:** Treasury, Model Risk Management, Compliance
