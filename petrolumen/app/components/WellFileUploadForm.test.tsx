import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WellFileUploadForm } from './WellFileUploadForm';
import { uploadWellData, UploadResponse } from '@/lib/backendClient';

vi.mock('@/lib/backendClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/backendClient')>();
  return {
    ...actual,
    uploadWellData: vi.fn(),
  };
});

describe('WellFileUploadForm Component', () => {
  const mockOnUploadSuccess = vi.fn();
  const mockSetIsLoadingGlobal = vi.fn();
  const mockSetErrorGlobal = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Render State', () => {
    it('mounts without crashing and renders well name input, file input, and upload button', () => {
      render(
        <WellFileUploadForm
          onUploadSuccess={mockOnUploadSuccess}
          setIsLoadingGlobal={mockSetIsLoadingGlobal}
          setErrorGlobal={mockSetErrorGlobal}
          isLoadingGlobal={false}
        />
      );

      expect(screen.getByText('Upload Well Data')).toBeInTheDocument();
      expect(screen.getByLabelText(/well name:/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/select csv file\(s\):/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /upload data/i })).toBeInTheDocument();
    });

    it('disables input fields and submit button when isLoadingGlobal is true', () => {
      render(
        <WellFileUploadForm
          onUploadSuccess={mockOnUploadSuccess}
          setIsLoadingGlobal={mockSetIsLoadingGlobal}
          setErrorGlobal={mockSetErrorGlobal}
          isLoadingGlobal={true}
        />
      );

      expect(screen.getByLabelText(/well name:/i)).toBeDisabled();
      expect(screen.getByLabelText(/select csv file\(s\):/i)).toBeDisabled();
      expect(screen.getByRole('button', { name: /upload data/i })).toBeDisabled();
    });
  });

  describe('Primary Interaction', () => {
    it('handles file selection, well name typing, and submits form successfully', async () => {
      const mockResponse: UploadResponse = {
        message: 'File uploaded successfully!',
        well_name: 'Well-01',
        files_processed: ['production.csv'],
      };

      vi.mocked(uploadWellData).mockResolvedValueOnce(mockResponse);

      const { container } = render(
        <WellFileUploadForm
          onUploadSuccess={mockOnUploadSuccess}
          setIsLoadingGlobal={mockSetIsLoadingGlobal}
          setErrorGlobal={mockSetErrorGlobal}
          isLoadingGlobal={false}
        />
      );

      const wellNameInput = screen.getByLabelText(/well name:/i);
      fireEvent.change(wellNameInput, { target: { value: 'Well-01' } });

      const file = new File(['date,rate\n2023-01-01,100'], 'production.csv', { type: 'text/csv' });
      const fileInput = screen.getByLabelText(/select csv file\(s\):/i);
      fireEvent.change(fileInput, { target: { files: [file] } });

      const form = container.querySelector('form')!;
      fireEvent.submit(form);

      await waitFor(() => {
        expect(mockSetIsLoadingGlobal).toHaveBeenCalledWith(true);
        expect(mockSetErrorGlobal).toHaveBeenCalledWith('');
        expect(uploadWellData).toHaveBeenCalledWith('Well-01', expect.anything());
        expect(mockOnUploadSuccess).toHaveBeenCalledWith(mockResponse, 'Well-01');
      });

      expect(screen.getByText('File uploaded successfully!')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('sets error global when submitting without selecting files', async () => {
      const { container } = render(
        <WellFileUploadForm
          onUploadSuccess={mockOnUploadSuccess}
          setIsLoadingGlobal={mockSetIsLoadingGlobal}
          setErrorGlobal={mockSetErrorGlobal}
          isLoadingGlobal={false}
        />
      );

      const form = container.querySelector('form')!;
      fireEvent.submit(form);

      expect(mockSetErrorGlobal).toHaveBeenCalledWith(
        'Please select files and enter a well name for upload.'
      );
      expect(uploadWellData).not.toHaveBeenCalled();
    });

    it('handles upload API error and displays failure status', async () => {
      vi.mocked(uploadWellData).mockRejectedValueOnce(new Error('Server storage full'));

      const { container } = render(
        <WellFileUploadForm
          onUploadSuccess={mockOnUploadSuccess}
          setIsLoadingGlobal={mockSetIsLoadingGlobal}
          setErrorGlobal={mockSetErrorGlobal}
          isLoadingGlobal={false}
        />
      );

      const file = new File(['content'], 'test.csv', { type: 'text/csv' });
      const fileInput = screen.getByLabelText(/select csv file\(s\):/i);
      fireEvent.change(fileInput, { target: { files: [file] } });

      const form = container.querySelector('form')!;
      fireEvent.submit(form);

      await waitFor(() => {
        expect(mockSetErrorGlobal).toHaveBeenCalledWith('Upload error: Server storage full');
      });

      expect(screen.getByText('Upload failed.')).toBeInTheDocument();
    });
  });
});
