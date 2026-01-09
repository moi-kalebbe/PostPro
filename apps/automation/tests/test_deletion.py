from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json

from apps.agencies.models import Agency
from apps.projects.models import Project
from apps.automation.models import Post, ActivityLog

User = get_user_model()

class PostDeletionTest(TestCase):
    def setUp(self):
        # Create Agency and User
        self.agency = Agency.objects.create(name="Test Agency")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
            agency=self.agency
        )
        
        # Create Project
        self.project = Project.objects.create(
            name="Test Project",
            agency=self.agency,
            wordpress_url="https://example.com",
            wordpress_username="admin",
            wordpress_app_password="encrypted_password"
        )
        
        # Create Post
        self.post = Post.objects.create(
            project=self.project,
            keyword="test keyword",
            title="Test Post Title",
            status=Post.Status.PUBLISHED,
            wordpress_post_id=123
        )
        
        self.client = Client()
        self.client.force_login(self.user)

    @patch('apps.projects.models.Project.get_wordpress_password')
    @patch('services.wordpress.WordPressService')
    def test_delete_single_post_with_wp(self, MockWPService, mock_get_password):
        # Setup mocks
        mock_get_password.return_value = "decrypted_password"
        mock_wp_instance = MockWPService.return_value
        mock_wp_instance.delete_post.return_value = {'success': True}

        # Create request
        url = reverse('automation:post_delete', args=[self.post.id])
        
        data = {'delete_from_wordpress': True}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}. Content: {response.content.decode()}")
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['deleted_from_wordpress'])
        
        # Verify DB deletion
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
        
        # Verify Activity Log
        self.assertTrue(ActivityLog.objects.filter(
            entity_id=str(self.post.id),
            action="POST_DELETED"
        ).exists())

        # Verify WP Service called
        MockWPService.assert_called_with(
            site_url="https://example.com",
            username="admin",
            app_password="decrypted_password"
        )
        mock_wp_instance.delete_post.assert_called_with(123)

    def test_delete_single_post_local_only(self):
        # Create another post
        post2 = Post.objects.create(
            project=self.project,
            keyword="local delete",
            title="Local Delete",
            status=Post.Status.DRAFT
        )
        
        url = reverse('automation:post_delete', args=[post2.id])
        data = {'delete_from_wordpress': False}
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
        self.assertFalse(Post.objects.filter(id=post2.id).exists())

    @patch('apps.projects.models.Project.get_wordpress_password')
    @patch('services.wordpress.WordPressService')
    def test_bulk_delete(self, MockWPService, mock_get_password):
        # Setup mocks
        mock_get_password.return_value = "decrypted_password"
        mock_wp_instance = MockWPService.return_value
        mock_wp_instance.delete_post.return_value = {'success': True}
        
        # Create posts
        p1 = Post.objects.create(project=self.project, keyword="p1", wordpress_post_id=101)
        p2 = Post.objects.create(project=self.project, keyword="p2", wordpress_post_id=102)
        
        post_ids = [str(p1.id), str(p2.id)]
        data = {
            'post_ids': post_ids,
            'delete_from_wordpress': True
        }
        
        url = reverse('automation:posts_bulk_delete')
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
        response_data = response.json()
        self.assertEqual(response_data['deleted_count'], 2)
        self.assertEqual(response_data['wp_deleted_count'], 2)
        
        self.assertFalse(Post.objects.filter(id__in=post_ids).exists())
        self.assertEqual(mock_wp_instance.delete_post.call_count, 2)
