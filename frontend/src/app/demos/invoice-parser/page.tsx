'use client';

import { useState } from 'react';
import { 
  DocumentTextIcon, 
  ArrowUpTrayIcon,
  SparklesIcon,
  BuildingOfficeIcon,
  CalendarIcon,
  HashtagIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import FileUpload from '@/components/demos/FileUpload';
import ProcessingButton from '@/components/demos/ProcessingButton';
import AlertMessage from '@/components/demos/AlertMessage';

interface InvoiceItem {
  description: string;
  quantity: number | null;
  unit_price: number | null;
  amount: number;
}

interface InvoiceData {
  is_invoice: boolean;
  vendor_name?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  items: InvoiceItem[];
  subtotal?: number;
  tax_amount?: number;
  total_amount?: number;
  currency?: string;
}

export default function InvoiceParserPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<InvoiceData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/invoice-parser/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to parse invoice');
      }

      const data = await response.json();
      setResult(data);
      
      if (!data.is_invoice) {
        setError("This document doesn't appear to be a standard invoice. Extraction might be incomplete.");
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during parsing');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <DocumentTextIcon className="w-8 h-8 text-emerald-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Invoice Parser
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Extract structured data from invoice images and PDFs using multimodal AI.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-4 space-y-6">
            <div className="card p-6 h-fit">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Upload Invoice</h2>
              <p className="text-sm text-gray-600 mb-6">Select an image (PNG, JPG) or PDF file</p>
              
              <div className="space-y-4">
                <FileUpload
                  selectedFile={file}
                  onFileSelect={handleFileSelect}
                  onFileRemove={() => setFile(null)}
                  disabled={isUploading}
                  placeholder="Drop your invoice here"
                  accept="application/pdf,image/png,image/jpeg,image/webp"
                  description="Supports PDF (Gemini) and Images (All providers)"
                />
                
                <ProcessingButton
                  isLoading={isUploading}
                  onClick={handleUpload}
                  disabled={!file}
                  icon={<ArrowUpTrayIcon className="w-5 h-5 mr-3" />}
                >
                  Analyze Invoice
                </ProcessingButton>

                {error && (
                  <AlertMessage 
                    type={result?.is_invoice === false ? "info" : "error"} 
                    message={error} 
                  />
                )}
              </div>
            </div>
            
            <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-6 shadow-sm mr-4">
              <h3 className="font-bold text-emerald-900 mb-4 flex items-center gap-2">
                <SparklesIcon className="h-5 w-5 text-emerald-600" />
                How it works
              </h3>
              <ul className="space-y-4 text-sm text-emerald-800/80">
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-200/50 flex items-center justify-center text-xs font-bold text-emerald-700">1</span>
                  Vision-enabled LLM "sees" the document layout and text.
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-200/50 flex items-center justify-center text-xs font-bold text-emerald-700">2</span>
                  Pydantic models ensure structured data extraction.
                </li>
                <li className="flex gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-200/50 flex items-center justify-center text-xs font-bold text-emerald-700">3</span>
                  Automated validation distinguishes invoices from other documents.
                </li>
              </ul>
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-8">
            {result && result.is_invoice ? (
              <div className="space-y-6">
                <div className="card overflow-hidden border-t-4 border-t-emerald-500">
                  <div className="p-6 sm:p-8">
                    <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-8">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <BuildingOfficeIcon className="h-6 w-6 text-gray-400" />
                          <h2 className="text-2xl font-bold text-gray-900">
                            {result.vendor_name || 'Unknown Vendor'}
                          </h2>
                        </div>
                        <p className="text-gray-500">Successfully extracted invoice data</p>
                      </div>
                      <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium border border-emerald-100">
                        <CheckCircleIcon className="h-4 w-4" />
                        Valid Invoice
                      </div>
                    </div>

                    {/* Header Info Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
                      <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5 mb-1 text-center">
                          <HashtagIcon className="h-3 w-3" />
                          Number
                        </p>
                        <p className="font-semibold text-gray-900">{result.invoice_number || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5 mb-1">
                          <CalendarIcon className="h-3 w-3" />
                          Date
                        </p>
                        <p className="font-semibold text-gray-900">{result.invoice_date || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5 mb-1">
                          <CalendarIcon className="h-3 w-3 text-emerald-600" />
                          Due Date
                        </p>
                        <p className="font-semibold text-gray-900">{result.due_date || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5 mb-1 text-center">
                          <CurrencyDollarIcon className="h-3 w-3 text-emerald-600" />
                          Total
                        </p>
                        <p className="text-xl font-bold text-emerald-600">
                          {result.currency} {result.total_amount?.toLocaleString(undefined, {minimumFractionDigits: 2})}
                        </p>
                      </div>
                    </div>

                    <div className="h-px bg-gray-100 w-full mb-8" />

                    {/* Table Section */}
                    <div className="mb-8">
                      <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                        Line Items
                      </h3>
                      <div className="border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
                        <table className="w-full text-sm text-left">
                          <thead className="bg-gray-50 text-gray-500 font-bold uppercase text-[10px] tracking-wider border-b border-gray-100">
                            <tr>
                              <th className="px-6 py-4">Description</th>
                              <th className="px-6 py-4 text-center">Qty</th>
                              <th className="px-6 py-4 text-right">Price</th>
                              <th className="px-6 py-4 text-right">Amount</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-50">
                            {result.items.map((item, i) => (
                              <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-gray-900">{item.description}</td>
                                <td className="px-6 py-4 text-center text-gray-600 font-mono">{item.quantity || '-'}</td>
                                <td className="px-6 py-4 text-right text-gray-600 font-mono">
                                  {item.unit_price ? item.unit_price.toLocaleString(undefined, {minimumFractionDigits: 2}) : '-'}
                                </td>
                                <td className="px-6 py-4 text-right font-bold text-gray-900 font-mono">
                                  {item.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Totals Section */}
                    <div className="flex justify-end">
                      <div className="w-full sm:w-72 space-y-3 bg-gray-50/50 p-6 rounded-2xl border border-gray-100">
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>Subtotal</span>
                          <span className="font-mono">{result.currency} {result.subtotal?.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                        </div>
                        <div className="flex justify-between text-sm text-gray-600">
                          <span>Tax Amount</span>
                          <span className="font-mono">{result.currency} {result.tax_amount?.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                        </div>
                        <div className="h-px bg-gray-200 w-full my-2" />
                        <div className="flex justify-between text-lg font-bold text-gray-900">
                          <span>Total</span>
                          <span className="text-emerald-600 font-mono">{result.currency} {result.total_amount?.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-[500px] flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-gray-200 rounded-[2.5rem] bg-white/50">
                <div className="h-24 w-24 bg-gray-100 rounded-full flex items-center justify-center mb-8 shadow-inner">
                  <DocumentTextIcon className="h-10 w-10 text-gray-400" />
                </div>
                <h3 className="text-2xl font-bold text-gray-800 mb-3">Ready to Analyze</h3>
                <p className="text-gray-500 max-w-sm mx-auto text-lg leading-relaxed">
                  Upload an invoice document to extract line items, totals, and more automatically.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
