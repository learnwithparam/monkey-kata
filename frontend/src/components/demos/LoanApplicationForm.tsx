import { useState } from 'react';
import { ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline';
import SubmitButton from './SubmitButton';
import AlertMessage from './AlertMessage';

interface LoanApplicationFormProps {
  onSubmit: (data: LoanApplicationData) => Promise<void>;
  isLoading: boolean;
}

export interface LoanApplicationData {
  applicant_name: string;
  loan_amount: number;
  annual_income: number;
  credit_score?: number;
  employment_status: string;
  loan_purpose: string;
  existing_debt: number;
}

export default function LoanApplicationForm({ onSubmit, isLoading }: LoanApplicationFormProps) {
  const [formData, setFormData] = useState<LoanApplicationData>({
    applicant_name: '',
    loan_amount: 0,
    annual_income: 0,
    credit_score: undefined,
    employment_status: 'employed',
    loan_purpose: '',
    existing_debt: 0,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof LoanApplicationData, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof LoanApplicationData, boolean>>>({});

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof LoanApplicationData, string>> = {};

    if (!formData.applicant_name.trim()) {
      newErrors.applicant_name = 'Applicant name is required';
    }

    if (!formData.loan_amount || formData.loan_amount <= 0) {
      newErrors.loan_amount = 'Loan amount must be greater than 0';
    } else if (formData.loan_amount < 1000) {
      newErrors.loan_amount = 'Loan amount must be at least $1,000';
    }

    if (!formData.annual_income || formData.annual_income <= 0) {
      newErrors.annual_income = 'Annual income is required and must be greater than 0';
    } else if (formData.annual_income < 10000) {
      newErrors.annual_income = 'Annual income must be at least $10,000';
    }

    if (formData.credit_score !== undefined) {
      if (isNaN(formData.credit_score) || formData.credit_score < 300 || formData.credit_score > 850) {
        newErrors.credit_score = 'Credit score must be between 300 and 850';
      }
    }

    if (!formData.loan_purpose.trim()) {
      newErrors.loan_purpose = 'Loan purpose is required';
    }

    if (formData.existing_debt < 0 || isNaN(formData.existing_debt)) {
      newErrors.existing_debt = 'Existing debt cannot be negative';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleBlur = (field: keyof LoanApplicationData) => {
    setTouched({ ...touched, [field]: true });
    validate();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      await onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="applicant_name" className="block text-sm font-semibold text-gray-700 mb-2">
          Applicant Name *
        </label>
        <input
          type="text"
          id="applicant_name"
          value={formData.applicant_name}
          onChange={(e) => setFormData({ ...formData, applicant_name: e.target.value })}
          onBlur={() => handleBlur('applicant_name')}
          className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 ${
            errors.applicant_name && touched.applicant_name ? 'border-red-300' : 'border-gray-200'
          }`}
          placeholder="Enter full name"
          disabled={isLoading}
          required
        />
        {errors.applicant_name && (
          <p className="mt-1 text-sm text-red-600">{errors.applicant_name}</p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="loan_amount" className="block text-sm font-semibold text-gray-700 mb-2">
            Loan Amount ($) *
          </label>
          <input
            type="number"
            id="loan_amount"
            value={formData.loan_amount || ''}
            onChange={(e) => {
              const value = e.target.value === '' ? 0 : parseFloat(e.target.value);
              setFormData({ ...formData, loan_amount: isNaN(value) ? 0 : value });
            }}
            onBlur={() => handleBlur('loan_amount')}
            className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 ${
              errors.loan_amount && touched.loan_amount ? 'border-red-300' : 'border-gray-200'
            }`}
            placeholder="50000"
            min="1000"
            step="1"
            disabled={isLoading}
            required
          />
          {errors.loan_amount && touched.loan_amount && (
            <p className="mt-1 text-sm text-red-600">{errors.loan_amount}</p>
          )}
        </div>

        <div>
          <label htmlFor="annual_income" className="block text-sm font-semibold text-gray-700 mb-2">
            Annual Income ($) *
          </label>
          <input
            type="number"
            id="annual_income"
            value={formData.annual_income || ''}
            onChange={(e) => {
              const value = e.target.value === '' ? 0 : parseFloat(e.target.value);
              setFormData({ ...formData, annual_income: isNaN(value) ? 0 : value });
            }}
            onBlur={() => handleBlur('annual_income')}
            className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 ${
              errors.annual_income && touched.annual_income ? 'border-red-300' : 'border-gray-200'
            }`}
            placeholder="75000"
            min="10000"
            step="1"
            disabled={isLoading}
            required
          />
          {errors.annual_income && touched.annual_income && (
            <p className="mt-1 text-sm text-red-600">{errors.annual_income}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="credit_score" className="block text-sm font-semibold text-gray-700 mb-2">
            Credit Score
          </label>
          <input
            type="number"
            id="credit_score"
            value={formData.credit_score || ''}
            onChange={(e) => {
              const value = e.target.value === '' ? undefined : parseInt(e.target.value);
              setFormData({ ...formData, credit_score: value && !isNaN(value) ? value : undefined });
            }}
            onBlur={() => handleBlur('credit_score')}
            className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 ${
              errors.credit_score && touched.credit_score ? 'border-red-300' : 'border-gray-200'
            }`}
            placeholder="300-850 (optional)"
            min="300"
            max="850"
            disabled={isLoading}
          />
          {errors.credit_score && touched.credit_score && (
            <p className="mt-1 text-sm text-red-600">{errors.credit_score}</p>
          )}
        </div>

        <div>
          <label htmlFor="existing_debt" className="block text-sm font-semibold text-gray-700 mb-2">
            Existing Debt ($)
          </label>
          <input
            type="number"
            id="existing_debt"
            value={formData.existing_debt || ''}
            onChange={(e) => {
              const value = e.target.value === '' ? 0 : parseFloat(e.target.value);
              setFormData({ ...formData, existing_debt: isNaN(value) ? 0 : Math.max(0, value) });
            }}
            onBlur={() => handleBlur('existing_debt')}
            className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 ${
              errors.existing_debt && touched.existing_debt ? 'border-red-300' : 'border-gray-200'
            }`}
            placeholder="0 (optional)"
            min="0"
            step="1"
            disabled={isLoading}
          />
          {errors.existing_debt && touched.existing_debt && (
            <p className="mt-1 text-sm text-red-600">{errors.existing_debt}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="employment_status" className="block text-sm font-semibold text-gray-700 mb-2">
          Employment Status *
        </label>
        <select
          id="employment_status"
          value={formData.employment_status}
          onChange={(e) => setFormData({ ...formData, employment_status: e.target.value })}
          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 bg-white hover:border-gray-300"
          disabled={isLoading}
        >
          <option value="employed">Employed</option>
          <option value="self-employed">Self-Employed</option>
          <option value="unemployed">Unemployed</option>
          <option value="retired">Retired</option>
        </select>
      </div>

      <div>
        <label htmlFor="loan_purpose" className="block text-sm font-semibold text-gray-700 mb-2">
          Loan Purpose *
        </label>
        <input
          type="text"
          id="loan_purpose"
          value={formData.loan_purpose}
          onChange={(e) => setFormData({ ...formData, loan_purpose: e.target.value })}
          onBlur={() => handleBlur('loan_purpose')}
          className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300 ${
            errors.loan_purpose && touched.loan_purpose ? 'border-red-300' : 'border-gray-200'
          }`}
          placeholder="e.g., Home improvement, Debt consolidation"
          disabled={isLoading}
          required
        />
        {errors.loan_purpose && touched.loan_purpose && (
          <p className="mt-1 text-sm text-red-600">{errors.loan_purpose}</p>
        )}
      </div>

      <SubmitButton isLoading={isLoading} disabled={isLoading}>
        <span className="flex items-center justify-center">
          <ClipboardDocumentCheckIcon className="w-5 h-5 mr-2" />
          Submit Application
        </span>
      </SubmitButton>
    </form>
  );
}

