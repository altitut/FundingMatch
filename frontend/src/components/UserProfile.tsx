import React, { useState, useEffect } from 'react';
import { Upload, FileText, Link, CheckCircle, AlertCircle, Plus, X, User, RefreshCw, Trash2, CheckCircle2, Edit } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5001/api';

interface UploadedFile {
  filename: string;
  path: string;
  type: 'pdf' | 'json';
}

interface UserDoc {
  name: string;
  status: string;
}

interface UserUrl {
  url: string;
  type: string;
  status: string;
}

interface ExistingUser {
  id: string;
  name: string;
  documents: UserDoc[];
  urls: UserUrl[];
}

const UserProfile: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [urls, setUrls] = useState<string[]>(['']);
  const [name, setName] = useState('');
  const [interests, setInterests] = useState('');
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | null; text: string }>({
    type: null,
    text: '',
  });
  const [isDragging, setIsDragging] = useState(false);
  const [existingUsers, setExistingUsers] = useState<ExistingUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [progress, setProgress] = useState<string>('');
  const [progressDetails, setProgressDetails] = useState<{
    current: number;
    total: number;
    percentage: number;
    currentItem?: any;
  } | null>(null);
  const [processedFiles, setProcessedFiles] = useState<any[]>([]);
  const [processingSummary, setProcessingSummary] = useState<{
    pdfs: number;
    urls: number;
    total: number;
  } | null>(null);
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [editFiles, setEditFiles] = useState<UploadedFile[]>([]);
  const [editUrls, setEditUrls] = useState<string[]>(['']);
  const [isEditDragging, setIsEditDragging] = useState(false);
  const [reprocessingUserId, setReprocessingUserId] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const response = await axios.get(`${API_BASE}/users`);
      if (response.data.success) {
        setExistingUsers(response.data.users);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    for (const file of droppedFiles) {
      if (file.name.endsWith('.pdf') || file.name.endsWith('.json')) {
        await uploadFile(file);
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles) {
      for (let i = 0; i < selectedFiles.length; i++) {
        await uploadFile(selectedFiles[i]);
      }
    }
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    setProgress(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/profile/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        const fileType = file.name.endsWith('.pdf') ? 'pdf' : 'json';
        setFiles([...files, {
          filename: response.data.filename,
          path: response.data.path,
          type: fileType,
        }]);
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to upload ${file.name}` });
    } finally {
      setUploading(false);
      setProgress('');
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const addUrlField = () => {
    setUrls([...urls, '']);
  };

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const removeUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const handleCreateProfile = async () => {
    if (!name.trim()) {
      setMessage({ type: 'error', text: 'Please enter your name' });
      return;
    }

    setCreating(true);
    setMessage({ type: null, text: '' });
    setProgress('Creating user profile...');
    setProgressDetails(null);
    setProcessedFiles([]);
    setProcessingSummary(null);

    try {
      // Calculate total items to process
      const totalItems = files.length + urls.filter(url => url.trim() !== '').length;
      let currentItem = 0;

      // Simulate processing files
      const processItems = async () => {
        const processedItems: any[] = [];

        // Process PDFs
        for (const file of files) {
          currentItem++;
          setProgressDetails({
            current: currentItem,
            total: totalItems,
            percentage: Math.round((currentItem / totalItems) * 100),
            currentItem: { title: file.filename, type: 'pdf' }
          });
          setProgress(`Processing PDF: ${file.filename}`);
          
          processedItems.push({
            title: file.filename,
            type: 'pdf',
            status: 'success',
            message: 'Extracted text and metadata'
          });
          setProcessedFiles([...processedItems]);
          
          // Small delay to show progress
          await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Process URLs
        const validUrls = urls.filter(url => url.trim() !== '');
        for (const url of validUrls) {
          currentItem++;
          setProgressDetails({
            current: currentItem,
            total: totalItems,
            percentage: Math.round((currentItem / totalItems) * 100),
            currentItem: { title: url, type: 'url' }
          });
          setProgress(`Fetching content from URL...`);
          
          processedItems.push({
            title: url,
            type: 'url',
            status: 'success',
            message: 'Fetched and analyzed content'
          });
          setProcessedFiles([...processedItems]);
          
          // Small delay to show progress
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      };

      // Start processing animation
      processItems();

      setMessage({ type: 'info', text: 'Processing documents and generating embeddings... This may take a minute.' });
      
      const response = await axios.post(`${API_BASE}/profile/create`, {
        files,
        urls: urls.filter(url => url.trim() !== ''),
        name: name.trim(),
        interests: interests.split(',').map(i => i.trim()).filter(i => i),
      }, {
        timeout: 180000, // 3 minute timeout
      });

      if (response.data.success) {
        // Set final summary
        setProcessingSummary({
          pdfs: files.length,
          urls: urls.filter(url => url.trim() !== '').length,
          total: totalItems
        });

        setMessage({
          type: 'success',
          text: `Profile created successfully! ${response.data.profile.documents_processed} documents processed.`,
        });
        
        // Reset form after a delay to show summary
        setTimeout(() => {
          setFiles([]);
          setUrls(['']);
          setName('');
          setInterests('');
          fetchUsers();
        }, 2000);
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to create profile' });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to create profile. Please ensure the server is running.',
      });
    } finally {
      setCreating(false);
      setProgress('');
      setProgressDetails(null);
    }
  };

  const handleRemoveDocument = async (userId: string, filename: string) => {
    try {
      const response = await axios.post(`${API_BASE}/profile/remove-document`, {
        user_id: userId,
        filename,
      });
      if (response.data.success) {
        fetchUsers();
      }
    } catch (error) {
      console.error('Failed to remove document:', error);
    }
  };

  const handleRemoveUrl = async (userId: string, url: string) => {
    try {
      const response = await axios.post(`${API_BASE}/profile/remove-url`, {
        user_id: userId,
        url,
      });
      if (response.data.success) {
        setMessage({ type: 'success', text: 'URL removed successfully' });
        fetchUsers();
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to remove URL' });
      }
    } catch (error) {
      console.error('Failed to remove URL:', error);
      setMessage({ type: 'error', text: 'Failed to remove URL. Please try again.' });
    }
  };

  const handleProcessUser = async (userId: string) => {
    // Find the user name for better feedback
    const user = existingUsers.find(u => u.id === userId);
    const userName = user?.name || 'User';
    
    setReprocessingUserId(userId);
    setMessage({ type: 'info', text: `Reprocessing profile for ${userName}...` });
    setProgress('Starting reprocessing...');
    
    try {
      // Add a longer timeout for reprocessing
      const response = await axios.post(`${API_BASE}/profile/process`, {
        user_id: userId,
        new_files: [],
      }, {
        timeout: 300000, // 5 minute timeout
        onUploadProgress: (progressEvent) => {
          setProgress('Processing documents and generating embeddings...');
        }
      });
      
      if (response.data.success) {
        setMessage({ 
          type: 'success', 
          text: `Profile for ${userName} reprocessed successfully. Documents: ${response.data.documents_processed || 0}, URLs: ${response.data.urls_processed || 0}` 
        });
        setProgress('');
        fetchUsers();
      } else {
        setMessage({ 
          type: 'error', 
          text: response.data.error || `Failed to reprocess profile for ${userName}` 
        });
        setProgress('');
      }
    } catch (error: any) {
      console.error('Reprocessing error:', error);
      let errorMessage = `Failed to reprocess profile for ${userName}`;
      
      if (error.response) {
        // Server responded with error
        errorMessage = error.response.data?.error || errorMessage;
        if (error.response.status === 500) {
          errorMessage += '. The server encountered an internal error.';
        }
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Reprocessing timed out. The profile may contain many documents. Please try again.';
      } else if (error.request) {
        errorMessage = 'Failed to connect to server. Please ensure the backend is running.';
      }
      
      setMessage({ type: 'error', text: errorMessage });
      setProgress('');
    } finally {
      setReprocessingUserId(null);
    }
  };

  const handleDeleteUser = async (userId: string, userName: string) => {
    if (!window.confirm(`Are you sure you want to delete user "${userName}"? This will remove all their data and cannot be undone.`)) {
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE}/users/${userId}`);
      
      if (response.data.success) {
        setMessage({
          type: 'success',
          text: `User "${userName}" has been deleted successfully`
        });
        // Refresh the users list
        fetchUsers();
      } else {
        setMessage({
          type: 'error',
          text: response.data.error || 'Failed to delete user'
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to delete user. Please try again.'
      });
    }
  };

  const startEditUser = (userId: string) => {
    setEditingUserId(userId);
    setEditFiles([]);
    setEditUrls(['']);
    setMessage({ type: null, text: '' });
  };

  const cancelEdit = () => {
    setEditingUserId(null);
    setEditFiles([]);
    setEditUrls(['']);
    setIsEditDragging(false);
  };

  const uploadEditFile = async (file: File) => {
    setUploading(true);
    setProgress(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/profile/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        const fileType = file.name.endsWith('.pdf') ? 'pdf' : 'json';
        setEditFiles([...editFiles, {
          filename: response.data.filename,
          path: response.data.path,
          type: fileType,
        }]);
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to upload ${file.name}` });
    } finally {
      setUploading(false);
      setProgress('');
    }
  };

  const handleEditFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles) {
      for (let i = 0; i < selectedFiles.length; i++) {
        await uploadEditFile(selectedFiles[i]);
      }
    }
  };

  const handleEditDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsEditDragging(true);
  };

  const handleEditDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsEditDragging(false);
  };

  const handleEditDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleEditDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsEditDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    for (const file of droppedFiles) {
      if (file.name.endsWith('.pdf') || file.name.endsWith('.json')) {
        await uploadEditFile(file);
      }
    }
  };

  const handleUpdateProfile = async () => {
    if (!editingUserId) return;

    setCreating(true);
    setMessage({ type: 'info', text: 'Updating user profile with new documents...' });

    try {
      // Get existing user data
      const user = existingUsers.find(u => u.id === editingUserId);
      if (!user) {
        throw new Error('User not found');
      }

      // Get all existing documents
      const existingDocs = user.documents.map(doc => ({
        filename: doc.name,
        path: `uploads/${doc.name}`,
        type: doc.name.endsWith('.pdf') ? 'pdf' as const : 'json' as const
      }));

      // Combine with new files
      const allFiles = [...existingDocs, ...editFiles];

      // Update profile with all documents
      const response = await axios.post(`${API_BASE}/profile/update`, {
        user_id: editingUserId,
        files: allFiles,
        urls: [...user.urls.map(u => u.url), ...editUrls.filter(url => url.trim() !== '')],
        add_only: true  // Only add new documents, don't remove existing ones
      }, {
        timeout: 180000, // 3 minute timeout
      });

      if (response.data.success) {
        const docsProcessed = response.data.documents_processed || 0;
        const urlsProcessed = response.data.urls_processed || 0;
        const totalProcessed = response.data.total_processed || (docsProcessed + urlsProcessed);
        
        let messageText = 'Profile updated successfully! ';
        if (totalProcessed > 0) {
          const parts = [];
          if (docsProcessed > 0) parts.push(`${docsProcessed} new document${docsProcessed !== 1 ? 's' : ''}`);
          if (urlsProcessed > 0) parts.push(`${urlsProcessed} new URL${urlsProcessed !== 1 ? 's' : ''}`);
          messageText += `Added ${parts.join(' and ')}.`;
        } else {
          messageText += 'No new items were added (all items may already exist).';
        }
        
        setMessage({
          type: 'success',
          text: messageText,
        });
        
        // Reset edit state
        cancelEdit();
        fetchUsers();
      } else {
        setMessage({ type: 'error', text: response.data.error || 'Failed to update profile' });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to update profile. Please ensure the server is running.',
      });
    } finally {
      setCreating(false);
      setProgress('');
    }
  };

  const updateEditUrl = (index: number, value: string) => {
    const newUrls = [...editUrls];
    newUrls[index] = value;
    setEditUrls(newUrls);
  };

  const removeEditUrl = (index: number) => {
    setEditUrls(editUrls.filter((_, i) => i !== index));
  };

  const addEditUrlField = () => {
    setEditUrls([...editUrls, '']);
  };

  const removeEditFile = (index: number) => {
    setEditFiles(editFiles.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">User Profile</h2>
        <p className="mt-2 text-gray-600">
          Upload your CV, research papers, and provide URLs to create a comprehensive profile.
          The system will extract information to match you with relevant funding opportunities.
        </p>
      </div>

      {/* Existing Users */}
      {existingUsers.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Existing Users</h3>
          {loadingUsers ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {existingUsers.map((user) => (
                <div key={user.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <User className="h-5 w-5 text-gray-400 mr-2" />
                      <h4 className="font-medium text-gray-900">{user.name}</h4>
                    </div>
                    <div className="flex items-center space-x-2">
                      {editingUserId !== user.id && (
                        <>
                          <button
                            onClick={() => startEditUser(user.id)}
                            className="text-indigo-600 hover:text-indigo-800 flex items-center text-sm"
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            Edit
                          </button>
                          <button
                            onClick={() => handleProcessUser(user.id)}
                            disabled={reprocessingUserId === user.id}
                            className={`flex items-center text-sm ${
                              reprocessingUserId === user.id 
                                ? 'text-gray-400 cursor-not-allowed' 
                                : 'text-indigo-600 hover:text-indigo-800'
                            }`}
                          >
                            <RefreshCw className={`h-4 w-4 mr-1 ${reprocessingUserId === user.id ? 'animate-spin' : ''}`} />
                            {reprocessingUserId === user.id ? 'Reprocessing...' : 'Reprocess'}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id, user.name)}
                            className="text-red-600 hover:text-red-800 flex items-center text-sm"
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {user.documents.length > 0 && (
                    <div className="mb-3">
                      <p className="text-sm font-medium text-gray-700 mb-1">Documents:</p>
                      <div className="space-y-1">
                        {user.documents.map((doc, idx) => (
                          <div key={idx} className="flex items-center justify-between bg-gray-50 rounded px-3 py-1">
                            <div className="flex items-center">
                              <FileText className="h-4 w-4 text-gray-400 mr-2" />
                              <span className="text-sm text-gray-600">{doc.name}</span>
                              <span className="ml-2 text-xs text-green-600">✓ {doc.status}</span>
                            </div>
                            {editingUserId === user.id && (
                              <button
                                onClick={() => handleRemoveDocument(user.id, doc.name)}
                                className="text-red-600 hover:text-red-800"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {user.urls.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">URLs:</p>
                      <div className="space-y-1">
                        {user.urls.map((url, idx) => (
                          <div key={idx} className="flex items-center justify-between bg-gray-50 rounded px-3 py-1">
                            <div className="flex items-center">
                              <Link className="h-4 w-4 text-gray-400 mr-2" />
                              <span className="text-sm text-gray-600 truncate">{url.url}</span>
                              <span className="ml-2 text-xs text-green-600">✓ {url.status}</span>
                            </div>
                            {editingUserId === user.id && (
                              <button
                                onClick={() => handleRemoveUrl(user.id, url.url)}
                                className="text-red-600 hover:text-red-800"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reprocessing Progress */}
                  {reprocessingUserId === user.id && progress && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2" />
                        <span className="text-sm text-blue-800">{progress}</span>
                      </div>
                    </div>
                  )}

                  {/* Edit Mode UI */}
                  {editingUserId === user.id && (
                    <div className="mt-4 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                      <h5 className="font-medium text-gray-900 mb-3">Add More Documents</h5>
                      
                      {/* File Upload */}
                      <div className="mb-4">
                        <div
                          className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
                            isEditDragging
                              ? 'border-indigo-500 bg-indigo-100'
                              : 'border-gray-300 hover:border-gray-400'
                          }`}
                          onDragEnter={handleEditDragEnter}
                          onDragLeave={handleEditDragLeave}
                          onDragOver={handleEditDragOver}
                          onDrop={handleEditDrop}
                        >
                          <Upload className="mx-auto h-8 w-8 text-gray-400" />
                          <p className="mt-1 text-xs text-gray-600">
                            Drag and drop PDF or JSON files here, or click to select
                          </p>
                          <input
                            type="file"
                            accept=".pdf,.json"
                            multiple
                            onChange={handleEditFileSelect}
                            className="hidden"
                            id={`edit-upload-${user.id}`}
                            disabled={uploading}
                          />
                          <label
                            htmlFor={`edit-upload-${user.id}`}
                            className={`mt-2 inline-flex items-center px-3 py-1 border border-gray-300 rounded-md shadow-sm text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 ${uploading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                          >
                            {uploading ? 'Uploading...' : 'Select Files'}
                          </label>
                        </div>

                        {editFiles.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {editFiles.map((file, index) => (
                              <div key={index} className="flex items-center justify-between bg-white rounded p-2">
                                <div className="flex items-center">
                                  <FileText className="h-4 w-4 text-gray-400 mr-2" />
                                  <span className="text-xs text-gray-900">{file.filename}</span>
                                </div>
                                <button
                                  onClick={() => removeEditFile(index)}
                                  className="text-red-600 hover:text-red-800"
                                >
                                  <X className="h-3 w-3" />
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* URL Input */}
                      <div className="mb-4">
                        <p className="text-xs font-medium text-gray-700 mb-2">Add URLs</p>
                        <div className="space-y-2">
                          {editUrls.map((url, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <Link className="h-4 w-4 text-gray-400" />
                              <input
                                type="url"
                                value={url}
                                onChange={(e) => updateEditUrl(index, e.target.value)}
                                className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                placeholder="https://example.com/profile"
                              />
                              {editUrls.length > 1 && (
                                <button
                                  onClick={() => removeEditUrl(index)}
                                  className="text-red-600 hover:text-red-800"
                                >
                                  <X className="h-3 w-3" />
                                </button>
                              )}
                            </div>
                          ))}
                          <button
                            onClick={addEditUrlField}
                            className="flex items-center text-xs text-indigo-600 hover:text-indigo-800"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            Add another URL
                          </button>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={cancelEdit}
                          className="px-3 py-1 text-xs border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleUpdateProfile}
                          disabled={creating || (editFiles.length === 0 && editUrls.filter(u => u.trim()).length === 0)}
                          className={`px-3 py-1 text-xs rounded-md text-white ${
                            creating || (editFiles.length === 0 && editUrls.filter(u => u.trim()).length === 0)
                              ? 'bg-gray-400 cursor-not-allowed'
                              : 'bg-indigo-600 hover:bg-indigo-700'
                          }`}
                        >
                          {creating ? 'Updating...' : 'Update Profile'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Basic Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter your full name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Research Interests
            </label>
            <textarea
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={3}
              placeholder="Enter your research interests, separated by commas (e.g., AI, Machine Learning, Biomedical Engineering)"
            />
          </div>
        </div>
      </div>

      {/* Document Upload */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Documents</h3>
        
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            Drag and drop PDF files or JSON profile here, or click to select
          </p>
          <input
            type="file"
            accept=".pdf,.json"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="doc-upload"
            disabled={uploading}
          />
          <label
            htmlFor="doc-upload"
            className={`mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 ${uploading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
          >
            {uploading ? 'Uploading...' : 'Select Files'}
          </label>
        </div>

        {files.length > 0 && (
          <div className="mt-4 space-y-2">
            {files.map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-900">{file.filename}</span>
                  <span className="ml-2 px-2 py-1 text-xs rounded-full bg-gray-200 text-gray-700">
                    {file.type.toUpperCase()}
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* URL Input */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile URLs</h3>
        <p className="text-sm text-gray-600 mb-4">
          Add links to your faculty page, Google Scholar, NSF awards, etc.
        </p>
        
        <div className="space-y-3">
          {urls.map((url, index) => (
            <div key={index} className="flex items-center space-x-2">
              <Link className="h-5 w-5 text-gray-400" />
              <input
                type="url"
                value={url}
                onChange={(e) => updateUrl(index, e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="https://example.com/your-profile"
              />
              {urls.length > 1 && (
                <button
                  onClick={() => removeUrl(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
          <button
            onClick={addUrlField}
            className="flex items-center text-sm text-indigo-600 hover:text-indigo-800"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add another URL
          </button>
        </div>
      </div>

      {/* Messages */}
      {message.text && (
        <div
          className={`p-4 rounded-lg flex items-start ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800'
              : message.type === 'error'
              ? 'bg-red-50 text-red-800'
              : 'bg-blue-50 text-blue-800'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          ) : message.type === 'error' ? (
            <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          ) : (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-2 flex-shrink-0" />
          )}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {/* Create Profile Button */}
      <div>
        <button
          onClick={handleCreateProfile}
          disabled={creating || !name.trim()}
          className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            creating || !name.trim()
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {creating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              {progress || 'Creating Profile...'}
            </>
          ) : (
            'Create Profile'
          )}
        </button>
        
        {/* Progress Bar and Processing Details */}
        {creating && progressDetails && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-blue-800">Processing Progress</p>
                <span className="text-sm text-blue-600">
                  {progressDetails.current} / {progressDetails.total} ({progressDetails.percentage}%)
                </span>
              </div>
              
              <div className="w-full bg-blue-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progressDetails.percentage}%` }}
                />
              </div>
              
              {progressDetails.currentItem && (
                <div className="mt-3 p-2 bg-white rounded border border-blue-200">
                  <p className="text-xs text-gray-700 truncate">
                    <span className="font-medium">Processing:</span> {progressDetails.currentItem.title}
                    <span className="ml-2 text-gray-500">({progressDetails.currentItem.type})</span>
                  </p>
                </div>
              )}
            </div>
            
            {/* Processed Files List */}
            {processedFiles.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-blue-800 mb-2">Processed Items:</p>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {processedFiles.slice(-5).map((item, idx) => (
                    <div key={idx} className="flex items-center text-xs p-2 bg-white rounded border border-gray-200">
                      {item.status === 'success' && <CheckCircle2 className="h-3 w-3 text-green-500 mr-2 flex-shrink-0" />}
                      <FileText className="h-3 w-3 text-gray-400 mr-2 flex-shrink-0" />
                      <span className="truncate flex-1">{item.title}</span>
                      <span className="text-gray-500 ml-2 flex-shrink-0 text-xs">{item.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Processing Summary */}
        {!creating && processingSummary && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-semibold text-gray-800 mb-3">Profile Creation Summary</h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-3 bg-white rounded border border-gray-200">
                <FileText className="h-5 w-5 text-blue-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-900">{processingSummary.pdfs}</p>
                <p className="text-xs text-gray-600">PDF Files</p>
              </div>
              <div className="text-center p-3 bg-white rounded border border-gray-200">
                <Link className="h-5 w-5 text-green-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-900">{processingSummary.urls}</p>
                <p className="text-xs text-gray-600">URLs</p>
              </div>
              <div className="text-center p-3 bg-white rounded border border-gray-200">
                <CheckCircle2 className="h-5 w-5 text-indigo-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-900">{processingSummary.total}</p>
                <p className="text-xs text-gray-600">Total Processed</p>
              </div>
            </div>
            
            <button
              onClick={() => {
                setProcessingSummary(null);
                setProcessedFiles([]);
              }}
              className="mt-3 text-sm text-gray-600 hover:text-gray-800"
            >
              Clear Summary
            </button>
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">Tips for Best Results</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Upload your most recent CV or resume (PDF format)</li>
          <li>• Include successful grant proposals if available</li>
          <li>• Add links to your faculty profile and Google Scholar</li>
          <li>• Provide detailed research interests for better matching</li>
          <li>• Include any research papers that showcase your expertise</li>
          <li>• <strong>JSON Profile:</strong> Upload a JSON file for bulk URL processing (see example: input_documents/alfredo_costilla_reyes.json)</li>
        </ul>
        <details className="mt-3">
          <summary className="text-sm font-semibold text-blue-900 cursor-pointer">JSON Profile Format</summary>
          <pre className="mt-2 text-xs bg-white p-3 rounded overflow-x-auto">{`{
  "person": {
    "name": "Your Name",
    "summary": "Brief bio",
    "links": [
      {
        "url": "https://example.com/profile",
        "type": "faculty_profile"
      },
      {
        "url": "https://scholar.google.com/...",
        "type": "academic_profile"
      }
    ],
    "biographical_information": {
      "research_interests": ["AI", "ML"],
      "education": [...],
      "awards": [...]
    }
  }
}`}</pre>
        </details>
      </div>
    </div>
  );
};

export default UserProfile;